"""Data feed: download and cache market data.

Repointed from the (removed) crypto ccxt execution layer to the VN advisory
data sources in `data.vn` (DNSE prices + cache). Same public interface so
existing backtest/knowledge-engine callers keep working:

    feed = DataFeed()                       # advisory source (DNSE + cache)
    df   = feed.fetch("HPG", "1d", 2000)    # OHLCV DataFrame indexed by time

`symbol` is now a VN ticker (e.g. "HPG", "FPT"), not a crypto pair.
`exchange_id` is accepted for backward-compatibility but ignored — data comes
from DNSE chart-api via the advisory source.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.source_factory import build_advisory_source

# Our timeframe labels → data.vn interval tokens (DNSE: 1,3,5,15,30,1H,1D,1W).
_TF_TO_INTERVAL = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
    "1h": "1H", "1H": "1H", "1d": "1D", "1D": "1D", "1w": "1W", "1W": "1W",
}


class DataFeed:
    """Download and cache OHLCV data from the VN advisory source (DNSE)."""

    def __init__(
        self,
        data_dir: str = "./data/raw",
        exchange_id: str = "dnse",  # kept for backward-compat; ignored
        source: Optional[StockDataSource] = None,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Advisory source already caches OHLCV (parquet); DataFeed adds a CSV
        # layer on top for the legacy backtest workflow.
        self.source = source or build_advisory_source()
        self.exchange_id = "dnse"

    def fetch(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 1000,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch OHLCV as DataFrame. Merges cache with fresh data if cache is stale."""
        cache_file = self.data_dir / f"{symbol.replace('/', '_')}_{timeframe}.csv"
        df_cache = None

        if use_cache and cache_file.exists():
            df_cache = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            now = pd.Timestamp.utcnow().tz_localize(None)
            last = df_cache.index[-1]
            if last.tzinfo is not None:
                last = last.tz_localize(None)
            stale_threshold = pd.Timedelta(minutes=timeframe_minutes + 30)
            if not df_cache.empty and (now - last) <= stale_threshold:
                logger.info(f"Loading fresh cached data: {cache_file}")
                return df_cache
            logger.info(f"Cache stale ({df_cache.index[-1]}), refreshing from DNSE")

        logger.info(f"Downloading {symbol} {timeframe} from DNSE")
        df = self._download(symbol, timeframe, limit, df_cache)
        if df is None or df.empty:
            logger.warning("No data returned")
            return df_cache if df_cache is not None else pd.DataFrame()

        if df_cache is not None and not df_cache.empty:
            df = pd.concat([df_cache, df])
            df = df[~df.index.duplicated(keep="last")]
            df.sort_index(inplace=True)

        if use_cache:
            df.to_csv(cache_file)
            logger.info(f"Saved cache: {cache_file} ({len(df)} rows)")

        return df

    # ------------------------------------------------------------------
    # Internal — acquire OHLCV from the advisory source + normalise shape
    # ------------------------------------------------------------------
    def _download(
        self, symbol: str, timeframe: str, limit: int, df_cache: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """Fetch `limit` bars from the advisory source → DataFrame indexed by time."""
        interval = _TF_TO_INTERVAL.get(timeframe, "1D")
        end = datetime.utcnow().date()
        # Incremental refresh from the last cached bar; otherwise look back far
        # enough to cover `limit` bars (×1.6 buffer for non-trading days).
        if df_cache is not None and not df_cache.empty:
            start = pd.Timestamp(df_cache.index[-1]).date()
        else:
            lookback_days = int(self._timeframe_to_minutes(timeframe) / 1440 * limit * 1.6) + 5
            start = end - timedelta(days=max(lookback_days, limit))

        raw = self.source.get_ohlcv(symbol, start.isoformat(), end.isoformat(), interval)
        if raw is None or raw.empty:
            return pd.DataFrame()

        df = raw.copy()
        time_col = "time" if "time" in df.columns else df.columns[0]
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.rename(columns={time_col: "timestamp"}).set_index("timestamp")
        cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
        return df[cols].tail(limit)

    @staticmethod
    def _timeframe_to_minutes(timeframe: str) -> int:
        """Convert timeframe string (e.g. '4h', '1d') to minutes."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        multipliers = {"m": 1, "h": 60, "d": 1440, "w": 10080}
        return value * multipliers.get(unit, 1)
