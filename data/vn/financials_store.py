"""Persistent store for VN30 financial statements (BS/IS/CF) → database.

Backend: PostgreSQL if TRADING_DB_URL is reachable, else SQLite fallback
(./data/vn_financials.db). Mirrors the dual-backend pattern in cache.py.

Schema — one row per (ticker, statement_type, period_type, period_label):
    items_json  = {item_id: value}      for that single period
    labels_json = {item_id: vn_label}   (statement-wide; repeated per row)
    period_end  = derived fiscal period end (year -> YYYY-12-31)
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

from loguru import logger

from data.vn.models import FinancialStatement

try:
    import psycopg2  # noqa: F401
    _PG_OK = True
except Exception:  # pragma: no cover
    _PG_OK = False


def latest_period_labels(fs: FinancialStatement, n: int) -> List[str]:
    """Return the n most-recent period labels present across all items (desc)."""
    labels = set()
    for per_map in fs.items.values():
        labels.update(per_map.keys())
    # labels like "2024" or "2024-Q3" — lexical desc works for both
    return sorted(labels, reverse=True)[:n]


def _period_end(period_label: str, period_type: str) -> str:
    """Derive an ISO period-end date from a label (best-effort)."""
    if period_type == "year" and period_label.isdigit():
        return f"{period_label}-12-31"
    # quarter labels like "2024-Q3"
    if "Q" in period_label:
        try:
            y, q = period_label.split("-Q")
            return f"{y}-{['03-31','06-30','09-30','12-31'][int(q) - 1]}"
        except Exception:
            return period_label
    return period_label


class FinancialsStore:
    """Upsert financial statements into PostgreSQL (or SQLite fallback)."""

    def __init__(self, db_url: Optional[str] = None, sqlite_path: str = "./data/vn_financials.db"):
        self.db_url = db_url or os.environ.get("TRADING_DB_URL")
        self._sqlite_path = Path(sqlite_path)
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.backend = "postgres" if (self.db_url and self.db_url.startswith("postgresql://")
                                       and _PG_OK and self._pg_reachable()) else "sqlite"
        self._init_table()
        logger.info(f"FinancialsStore ready (backend={self.backend})")

    def _pg_reachable(self) -> bool:
        try:
            import psycopg2
            psycopg2.connect(self.db_url, connect_timeout=4).close()
            return True
        except Exception as exc:
            logger.warning(f"PostgreSQL unreachable ({str(exc)[:50]}) — using SQLite fallback")
            return False

    @contextmanager
    def _connect(self):
        if self.backend == "postgres":
            import psycopg2
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

    def _init_table(self):
        ddl = """
            CREATE TABLE IF NOT EXISTS vn_financials (
                ticker         TEXT NOT NULL,
                statement_type TEXT NOT NULL,
                period_type    TEXT NOT NULL,
                period_label   TEXT NOT NULL,
                period_end     TEXT,
                items_json     TEXT NOT NULL,
                labels_json    TEXT NOT NULL,
                source         TEXT,
                fetched_at     DOUBLE PRECISION NOT NULL,
                PRIMARY KEY (ticker, statement_type, period_type, period_label)
            )
        """
        if self.backend == "sqlite":
            ddl = ddl.replace("DOUBLE PRECISION", "REAL")
        with self._connect() as conn:
            conn.cursor().execute(ddl) if self.backend == "postgres" else conn.execute(ddl)
            conn.commit()

    def store_statement(self, fs: FinancialStatement, max_periods: int, source: str = "vnstock-VCI") -> int:
        """Upsert the latest `max_periods` of a statement. Returns rows written."""
        if not fs.items:
            return 0
        labels = latest_period_labels(fs, max_periods)
        ph = self._ph()
        upsert = (
            f"INSERT INTO vn_financials "
            f"(ticker,statement_type,period_type,period_label,period_end,items_json,labels_json,source,fetched_at) "
            f"VALUES ({','.join([ph]*9)}) "
            + ("ON CONFLICT (ticker,statement_type,period_type,period_label) DO UPDATE SET "
               "period_end=EXCLUDED.period_end,items_json=EXCLUDED.items_json,"
               "labels_json=EXCLUDED.labels_json,source=EXCLUDED.source,fetched_at=EXCLUDED.fetched_at"
               if self.backend == "postgres" else "")
        )
        if self.backend == "sqlite":
            upsert = upsert.replace("INSERT INTO", "INSERT OR REPLACE INTO")
        now = time.time()
        labels_json = json.dumps(fs.labels, ensure_ascii=False)
        written = 0
        with self._connect() as conn:
            cur = conn.cursor()
            for label in labels:
                items = {iid: per[label] for iid, per in fs.items.items() if label in per}
                if not items:
                    continue
                cur.execute(upsert, (
                    fs.ticker, fs.statement_type, fs.period, label,
                    _period_end(label, fs.period),
                    json.dumps(items, ensure_ascii=False), labels_json, source, now,
                ))
                written += 1
            conn.commit()
        return written

    def count(self) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM vn_financials")
            return cur.fetchone()[0]

    def get_ticker_financials(self, ticker: str, period_type: str = "year") -> dict:
        """Return stored statements for a ticker, shaped for display.

        {statement_type: {"periods": [labels desc],
                           "labels": {item_id: vn_label},
                           "values": {item_id: {period_label: value}}}}
        """
        ph = self._ph()
        sql = (f"SELECT statement_type, period_label, items_json, labels_json "
               f"FROM vn_financials WHERE ticker={ph} AND period_type={ph} "
               f"ORDER BY statement_type, period_label DESC")
        out: dict = {}
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, (ticker.upper(), period_type))
            rows = cur.fetchall()
        for stmt, label, items_json, labels_json in rows:
            s = out.setdefault(stmt, {"periods": [], "labels": {}, "values": {}})
            if label not in s["periods"]:
                s["periods"].append(label)
            if not s["labels"]:
                s["labels"] = json.loads(labels_json)
            for item_id, val in json.loads(items_json).items():
                s["values"].setdefault(item_id, {})[label] = val
        return out
