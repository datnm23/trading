"""Recommendation journal — dual-backend (SQLite / PostgreSQL), lazy connect.

Tables:
  recommendations  — log of advisory outputs per ticker
  paper_positions  — paper trading positions linked to recommendations

Auto-detects backend from db_url prefix (postgresql://...).
Never connects at import or instantiation time — first DB call is lazy.

Usage:
    # SQLite (default / offline)
    jnl = RecommendationLogger()
    rec_id = jnl.log_recommendation("FPT", "2026-06-15", "BUY", ...)
    pos_id = jnl.open_paper_position("FPT", "2026-06-15", 73_500, 100, rec_id)
    jnl.close_paper_position(pos_id, "2026-07-01", 80_000)

    # PostgreSQL
    jnl = RecommendationLogger(db_url="postgresql://user:pw@host/db")
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from loguru import logger

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor  # noqa: F401
    _PSYCOPG2_OK = True
except ImportError:
    _PSYCOPG2_OK = False

_DEFAULT_SQLITE = "./data/recommendations.db"


class RecommendationLogger:
    """Dual-backend recommendation + paper portfolio journal.

    Lazy connection: no DB I/O until first method call.
    """

    def __init__(
        self,
        db_path: str = _DEFAULT_SQLITE,
        db_url: Optional[str] = None,
    ) -> None:
        url = db_url or os.environ.get("TRADING_DB_URL")
        if url and url.startswith("postgresql://"):
            if not _PSYCOPG2_OK:
                logger.warning("psycopg2 not available — falling back to SQLite")
                self.backend = "sqlite"
                self.db_path = Path(db_path)
                self._pg_cfg: Dict[str, Any] = {}
            else:
                self.backend = "postgres"
                self.db_path = None  # type: ignore[assignment]
                parsed = urlparse(url)
                self._pg_cfg = {
                    "host": parsed.hostname or "localhost",
                    "port": parsed.port or 5432,
                    "dbname": parsed.path.lstrip("/") or "trading_journal",
                    "user": parsed.username or "trader",
                    "password": parsed.password or "",
                }
        else:
            self.backend = "sqlite"
            self.db_path = Path(db_path)
            self._pg_cfg = {}

        self._initialised = False  # tables created lazily

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self):
        self._ensure_init()
        if self.backend == "postgres":
            conn = psycopg2.connect(**self._pg_cfg)
            try:
                yield conn
            finally:
                conn.close()
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _ph(self) -> str:
        return "%s" if self.backend == "postgres" else "?"

    def _fetchall(self, cur) -> List[Dict[str, Any]]:
        if self.backend == "postgres":
            rows = cur.fetchall()
            if not rows:
                return []
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(r) for r in (cur.fetchall() or [])]

    def _lastrowid(self, cur) -> int:
        if self.backend == "postgres":
            row = cur.fetchone()
            return row[0] if row else 0
        return cur.lastrowid

    def _dt(self, dt: datetime) -> Any:
        return dt if self.backend == "postgres" else dt.isoformat()

    # ------------------------------------------------------------------
    # Lazy init
    # ------------------------------------------------------------------

    def _ensure_init(self) -> None:
        if self._initialised:
            return
        if self.backend == "sqlite":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._init_sqlite(conn)
            conn.close()
        else:
            conn = psycopg2.connect(**self._pg_cfg)
            self._init_postgres(conn)
            conn.close()
        self._initialised = True

    def _init_sqlite(self, conn) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker      TEXT NOT NULL,
                date        TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                target_price   REAL,
                current_price  REAL,
                score          INTEGER,
                upside_pct     REAL,
                reasons        TEXT,
                created_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_rec_ticker ON recommendations(ticker);
            CREATE INDEX IF NOT EXISTS idx_rec_date   ON recommendations(date);

            CREATE TABLE IF NOT EXISTS paper_positions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker            TEXT NOT NULL,
                entry_date        TEXT NOT NULL,
                entry_price       REAL NOT NULL,
                shares            REAL NOT NULL,
                recommendation_id INTEGER REFERENCES recommendations(id),
                status            TEXT NOT NULL DEFAULT 'open',
                exit_date         TEXT,
                exit_price        REAL,
                pnl               REAL
            );
            CREATE INDEX IF NOT EXISTS idx_pos_ticker ON paper_positions(ticker);
            CREATE INDEX IF NOT EXISTS idx_pos_status ON paper_positions(status);
        """)
        conn.commit()
        logger.info(f"RecommendationLogger initialised (SQLite) at {self.db_path}")

    def _init_postgres(self, conn) -> None:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id              SERIAL PRIMARY KEY,
                ticker          VARCHAR(20) NOT NULL,
                date            DATE NOT NULL,
                recommendation  VARCHAR(10) NOT NULL,
                target_price    NUMERIC(20,2),
                current_price   NUMERIC(20,2),
                score           INTEGER,
                upside_pct      NUMERIC(10,4),
                reasons         TEXT,
                created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_rec_ticker ON recommendations(ticker)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_rec_date   ON recommendations(date)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paper_positions (
                id                SERIAL PRIMARY KEY,
                ticker            VARCHAR(20) NOT NULL,
                entry_date        DATE NOT NULL,
                entry_price       NUMERIC(20,2) NOT NULL,
                shares            NUMERIC(20,4) NOT NULL,
                recommendation_id INTEGER REFERENCES recommendations(id),
                status            VARCHAR(10) NOT NULL DEFAULT 'open',
                exit_date         DATE,
                exit_price        NUMERIC(20,2),
                pnl               NUMERIC(20,2)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pos_ticker ON paper_positions(ticker)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pos_status ON paper_positions(status)")
        conn.commit()
        logger.info(f"RecommendationLogger initialised (PostgreSQL) at {self._pg_cfg.get('host')}")

    # ------------------------------------------------------------------
    # Recommendation CRUD
    # ------------------------------------------------------------------

    def log_recommendation(
        self,
        ticker: str,
        date: str,
        recommendation: str,
        *,
        target_price: Optional[float] = None,
        current_price: Optional[float] = None,
        score: Optional[int] = None,
        upside_pct: Optional[float] = None,
        reasons: Optional[List[str]] = None,
    ) -> int:
        """Insert a recommendation record; returns new id."""
        ph = self._ph()
        reasons_txt = json.dumps(reasons or [], ensure_ascii=False)
        now = self._dt(datetime.now())

        if self.backend == "postgres":
            sql = f"""
                INSERT INTO recommendations
                    (ticker, date, recommendation, target_price, current_price,
                     score, upside_pct, reasons, created_at)
                VALUES ({','.join([ph]*9)})
                RETURNING id
            """
        else:
            sql = f"""
                INSERT INTO recommendations
                    (ticker, date, recommendation, target_price, current_price,
                     score, upside_pct, reasons, created_at)
                VALUES ({','.join([ph]*9)})
            """

        params = (ticker, date, recommendation, target_price, current_price,
                  score, upside_pct, reasons_txt, now)

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            rec_id = self._lastrowid(cur)
            logger.info(f"Logged recommendation [{rec_id}] {ticker} {recommendation} score={score}")
            return rec_id

    def get_recommendations(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return recommendations as dicts, newest first."""
        ph = self._ph()
        sql = "SELECT * FROM recommendations WHERE 1=1"
        params: List[Any] = []
        if ticker:
            sql += f" AND ticker = {ph}"
            params.append(ticker)
        sql += f" ORDER BY created_at DESC LIMIT {ph}"
        params.append(limit)

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = self._fetchall(cur)

        result = []
        for r in rows:
            reasons_raw = r.get("reasons") or "[]"
            try:
                reasons = json.loads(reasons_raw)
            except (json.JSONDecodeError, TypeError):
                reasons = []
            r["reasons"] = reasons
            # normalise datetime to str
            for key in ("created_at",):
                if isinstance(r.get(key), datetime):
                    r[key] = r[key].isoformat()
            result.append(r)
        return result

    # ------------------------------------------------------------------
    # Paper portfolio
    # ------------------------------------------------------------------

    def open_paper_position(
        self,
        ticker: str,
        entry_date: str,
        entry_price: float,
        shares: float,
        recommendation_id: Optional[int] = None,
    ) -> int:
        """Open a paper position; returns new id."""
        ph = self._ph()
        if self.backend == "postgres":
            sql = f"""
                INSERT INTO paper_positions
                    (ticker, entry_date, entry_price, shares, recommendation_id, status)
                VALUES ({','.join([ph]*6)})
                RETURNING id
            """
        else:
            sql = f"""
                INSERT INTO paper_positions
                    (ticker, entry_date, entry_price, shares, recommendation_id, status)
                VALUES ({','.join([ph]*6)})
            """
        params = (ticker, entry_date, entry_price, shares, recommendation_id, "open")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            pos_id = self._lastrowid(cur)
            logger.info(f"Opened paper position [{pos_id}] {ticker} x{shares} @ {entry_price}")
            return pos_id

    def close_paper_position(
        self,
        position_id: int,
        exit_date: str,
        exit_price: float,
    ) -> bool:
        """Close a paper position and compute P&L. Returns True on success."""
        ph = self._ph()
        # Fetch entry data first
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT entry_price, shares FROM paper_positions WHERE id = {ph}", (position_id,))
            row = self._fetchall(cur)
            if not row:
                logger.warning(f"Paper position {position_id} not found")
                return False
            entry_price = float(row[0]["entry_price"])
            shares = float(row[0]["shares"])
            pnl = (exit_price - entry_price) * shares

            cur.execute(
                f"UPDATE paper_positions SET status={ph}, exit_date={ph}, exit_price={ph}, pnl={ph} WHERE id={ph}",
                ("closed", exit_date, exit_price, pnl, position_id),
            )
            conn.commit()
            logger.info(f"Closed paper position [{position_id}] pnl={pnl:+.2f}")
            return cur.rowcount > 0

    def get_paper_portfolio(
        self,
        status: Optional[str] = None,
        ticker: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Return paper positions as dicts."""
        ph = self._ph()
        sql = "SELECT * FROM paper_positions WHERE 1=1"
        params: List[Any] = []
        if status:
            sql += f" AND status = {ph}"
            params.append(status)
        if ticker:
            sql += f" AND ticker = {ph}"
            params.append(ticker)
        sql += f" ORDER BY entry_date DESC LIMIT {ph}"
        params.append(limit)

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return self._fetchall(cur)
