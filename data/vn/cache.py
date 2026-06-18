"""CachedDataSource — caching wrapper over any StockDataSource.

Storage backends:
  - OHLCV       → Parquet files at {cache_dir}/ohlcv/{ticker}.parquet
  - Financials / Ratios / Company → KV table 'vn_cache' in Postgres (JSONB) or SQLite

TTL (seconds) per data kind:
  ohlcv:        900       (15 min — for intraday refresh)
  financials:   7776000   (~90 days — quarterly cadence)
  ratios:       7776000
  company:      86400     (1 day)

Cache key format: "{ticker}:{kind}:{period}"
  e.g. "FPT:balance_sheet:year", "FPT:ohlcv:1D", "FPT:ratios:year", "FPT:company:"

OHLCV wide-window strategy (C1):
  On MISS, fetch a fixed wide window [history_start, today] and cache the full frame.
  On read, return HIT only if the requested [start, end] is fully covered by the
  cached frame's date span AND the file is within TTL — otherwise refetch the wide
  window. The returned DataFrame is always sliced to the requested [start, end].
"""

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios

try:
    import psycopg2
    _POSTGRES_AVAILABLE = True
except ImportError:
    _POSTGRES_AVAILABLE = False

# Default TTLs in seconds
DEFAULT_TTL: Dict[str, int] = {
    "ohlcv": 900,
    "financials": 7_776_000,
    "ratios": 7_776_000,
    "company": 86_400,
}

_KIND_TTL_MAP = {
    "balance_sheet": "financials",
    "income_statement": "financials",
    "cash_flow": "financials",
    "ratios": "ratios",
    "company": "company",
    "ohlcv": "ohlcv",
}

# Default start of wide OHLCV history window (configurable per-instance)
_DEFAULT_HISTORY_START = "2015-01-01"


def _ttl_key(kind: str) -> str:
    return _KIND_TTL_MAP.get(kind, "financials")


class CachedDataSource(StockDataSource):
    """Wraps a StockDataSource with TTL-aware caching.

    Args:
        source: Underlying data source.
        cache_dir: Directory for parquet files and SQLite fallback.
        db_url: Optional Postgres URL (TRADING_DB_URL). Falls back to SQLite if None.
        ttl: Dict mapping ttl-kind -> seconds (overrides defaults).
        history_start: Earliest date for the wide OHLCV fetch window (YYYY-MM-DD).
    """

    def __init__(
        self,
        source: StockDataSource,
        cache_dir: str = "./data/vn_cache",
        db_url: Optional[str] = None,
        ttl: Optional[Dict[str, int]] = None,
        history_start: str = _DEFAULT_HISTORY_START,
    ):
        self.source = source
        self.cache_dir = Path(cache_dir)
        self.db_url = db_url or os.environ.get("TRADING_DB_URL")
        self.ttl = {**DEFAULT_TTL, **(ttl or {})}
        self.history_start = history_start

        # Determine backend
        self.backend = (
            "postgres"
            if (self.db_url and self.db_url.startswith("postgresql://") and _POSTGRES_AVAILABLE)
            else "sqlite"
        )

        self._ohlcv_dir = self.cache_dir / "ohlcv"
        self._ohlcv_dir.mkdir(parents=True, exist_ok=True)
        self._sqlite_path = self.cache_dir / "vn_cache.db"

        if self.backend == "postgres":
            self._init_pg_table()
        else:
            self._init_sqlite_table()

        logger.info(f"CachedDataSource ready (backend={self.backend}, dir={self.cache_dir})")

    # ------------------------------------------------------------------
    # DB connectivity
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self):
        if self.backend == "postgres":
            conn = psycopg2.connect(self.db_url)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(str(self._sqlite_path), check_same_thread=False)
            try:
                yield conn
            finally:
                conn.close()

    def _ph(self) -> str:
        return "%s" if self.backend == "postgres" else "?"

    def _init_pg_table(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vn_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    fetched_at DOUBLE PRECISION NOT NULL
                )
            """)
            conn.commit()

    def _init_sqlite_table(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vn_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    fetched_at REAL NOT NULL
                )
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # KV get/set
    # ------------------------------------------------------------------

    def _kv_get(self, key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
        """Return cached payload dict if fresh, else None.

        Treats corrupt (non-deserializable) rows as MISS so they are
        transparently refetched rather than erroring forever (M5).
        """
        ph = self._ph()
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT payload, fetched_at FROM vn_cache WHERE cache_key = {ph}",
                    (key,),
                )
                row = cur.fetchone()
        except Exception as exc:
            logger.warning(f"Cache read error for {key!r}: {exc}")
            return None

        if row is None:
            return None
        payload_str, fetched_at = row
        age = time.time() - float(fetched_at)
        if age > ttl_seconds:
            logger.debug(f"Cache STALE [{key}] age={age:.0f}s ttl={ttl_seconds}s")
            return None
        try:
            return json.loads(payload_str)
        except (json.JSONDecodeError, Exception) as exc:
            # M5: corrupt row — treat as MISS, will refetch and overwrite
            logger.warning(f"Cache CORRUPT [{key}] — treating as MISS: {exc}")
            return None

    def _kv_set(self, key: str, data: Dict[str, Any]) -> None:
        ph = self._ph()
        payload_str = json.dumps(data, ensure_ascii=False)
        now = time.time()
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                if self.backend == "postgres":
                    cur.execute(
                        f"""
                        INSERT INTO vn_cache (cache_key, payload, fetched_at)
                        VALUES ({ph}, {ph}, {ph})
                        ON CONFLICT (cache_key)
                        DO UPDATE SET payload = EXCLUDED.payload, fetched_at = EXCLUDED.fetched_at
                        """,
                        (key, payload_str, now),
                    )
                else:
                    cur.execute(
                        f"""
                        INSERT OR REPLACE INTO vn_cache (cache_key, payload, fetched_at)
                        VALUES ({ph}, {ph}, {ph})
                        """,
                        (key, payload_str, now),
                    )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Cache write error for {key!r}: {exc}")

    # ------------------------------------------------------------------
    # OHLCV parquet cache — wide-window strategy
    # ------------------------------------------------------------------

    def _ohlcv_path(self, ticker: str) -> Path:
        return self._ohlcv_dir / f"{ticker}.parquet"

    def _ohlcv_cache_get(
        self, ticker: str, start: str, end: str, ttl_seconds: int
    ) -> Optional[pd.DataFrame]:
        """Return sliced DataFrame if cache covers [start, end] and is within TTL.

        Returns None (MISS) if:
          - file does not exist
          - file is older than TTL
          - cached frame's date span does not fully cover [start, end]
        """
        path = self._ohlcv_path(ticker)
        if not path.exists():
            return None

        age = time.time() - path.stat().st_mtime
        if age > ttl_seconds:
            logger.debug(f"OHLCV cache STALE [{ticker}] age={age:.0f}s")
            return None

        try:
            df = pd.read_parquet(str(path))
        except Exception as exc:
            logger.warning(f"OHLCV parquet read error [{ticker}]: {exc}")
            return None

        if df.empty or "time" not in df.columns:
            return None

        req_start = pd.Timestamp(start)
        req_end = pd.Timestamp(end)
        cached_min = df["time"].min()
        cached_max = df["time"].max()

        # Trailing-gap waiver: a "give me data up to today" request (req_end = today)
        # never matches cached_max when today/weekend/holiday has no bar yet — the
        # cache already holds every bar up to the last trading day, so refetching
        # produces nothing newer. We've already passed the TTL gate (file is fresh),
        # so treat a small trailing gap (<= 5 days) as covered to avoid perpetual
        # MISS → wide-window refetch on every recent-price lookup.
        # (Backtest as-of requests use a historical req_end <= cached_max, unaffected.)
        trailing_gap_days = (req_end - cached_max).days
        if cached_min > req_start or (cached_max < req_end and trailing_gap_days > 5):
            logger.debug(
                f"OHLCV cache PARTIAL [{ticker}] cached=[{cached_min.date()},{cached_max.date()}]"
                f" requested=[{req_start.date()},{req_end.date()}] — MISS"
            )
            return None

        # Clamp the slice upper bound to what we actually have (cached_max) so a
        # waived trailing gap still returns the latest available bars.
        req_end = min(req_end, cached_max)

        mask = (df["time"] >= req_start) & (df["time"] <= req_end)
        result = df[mask].reset_index(drop=True)
        logger.debug(f"OHLCV cache HIT [{ticker}] rows={len(result)}")
        return result

    def _ohlcv_cache_set(self, ticker: str, df: pd.DataFrame) -> None:
        path = self._ohlcv_path(ticker)
        try:
            df.to_parquet(str(path), index=False)
            logger.debug(f"OHLCV cache SET [{ticker}] rows={len(df)}")
        except Exception as exc:
            logger.warning(f"OHLCV parquet write error [{ticker}]: {exc}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_ohlcv(
        self, ticker: str, start: str, end: str, interval: str = "1D"
    ) -> pd.DataFrame:
        """Return OHLCV for [start, end], using wide-window parquet cache.

        On MISS, fetches [history_start, today] from the source and caches the
        full frame. Always returns only rows within the requested [start, end].
        """
        ttl = self.ttl["ohlcv"]
        cached = self._ohlcv_cache_get(ticker, start, end, ttl)
        if cached is not None:
            return cached

        # MISS — fetch a wide window to make future narrower requests cheap
        today = pd.Timestamp.now().strftime("%Y-%m-%d")
        fetch_start = self.history_start
        fetch_end = today

        logger.debug(
            f"OHLCV cache MISS [{ticker}] — fetching wide window [{fetch_start}, {fetch_end}]"
        )
        wide_df = self.source.get_ohlcv(ticker, fetch_start, fetch_end, interval)
        if not wide_df.empty:
            self._ohlcv_cache_set(ticker, wide_df)

        # Slice to the originally requested range for the return value
        if wide_df.empty or "time" not in wide_df.columns:
            return wide_df

        req_start = pd.Timestamp(start)
        req_end = pd.Timestamp(end)
        mask = (wide_df["time"] >= req_start) & (wide_df["time"] <= req_end)
        return wide_df[mask].reset_index(drop=True)

    def get_financials(
        self, ticker: str, statement_type: str, period: str = "year"
    ) -> FinancialStatement:
        key = f"{ticker}:{statement_type}:{period}"
        ttl = self.ttl["financials"]
        cached = self._kv_get(key, ttl)
        if cached is not None:
            logger.debug(f"Cache HIT [{key}]")
            return FinancialStatement.from_dict(cached)

        logger.debug(f"Cache MISS [{key}]")
        result = self.source.get_financials(ticker, statement_type, period)
        self._kv_set(key, result.to_dict())
        return result

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        key = f"{ticker}:ratios:{period}"
        ttl = self.ttl["ratios"]
        cached = self._kv_get(key, ttl)
        if cached is not None:
            logger.debug(f"Cache HIT [{key}]")
            return Ratios.from_dict(cached)

        logger.debug(f"Cache MISS [{key}]")
        result = self.source.get_ratios(ticker, period)
        self._kv_set(key, result.to_dict())
        return result

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        key = f"{ticker}:company:"
        ttl = self.ttl["company"]
        cached = self._kv_get(key, ttl)
        if cached is not None:
            logger.debug(f"Cache HIT [{key}]")
            return CompanyInfo.from_dict(cached)

        logger.debug(f"Cache MISS [{key}]")
        result = self.source.get_company(ticker)
        if result is not None:
            self._kv_set(key, result.to_dict())
        return result
