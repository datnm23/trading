"""Collect VN30 financial statements (BS/IS/CF) → database.

Scope: VN30, last N fiscal years (default 2), annual. Source: vnstock free
(VCI) — serves the most-recent ~4 periods, which covers 2 years for VN30.
Storage: PostgreSQL if TRADING_DB_URL reachable, else SQLite fallback.

Run: python3 scripts/collect_vn30_financials.py [years]
"""
from __future__ import annotations

import sys
import warnings

warnings.filterwarnings("ignore")

from loguru import logger

from data.vn.universe import get_vn30
from data.vn.vnstock_source import VnstockSource
from data.vn.financials_store import FinancialsStore

STATEMENTS = ["balance_sheet", "income_statement", "cash_flow"]


def main() -> int:
    years = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    tickers = get_vn30()
    # Throttle 5s to stay under vnstock guest limit (20 req/min); 30 tickers x 3
    # statements = 90 calls.
    src = VnstockSource(source="VCI", throttle_seconds=5.0)
    store = FinancialsStore()

    logger.info(f"Collecting {len(tickers)} VN30 tickers x {len(STATEMENTS)} statements, last {years}y")
    total_rows = 0
    failed = []
    for i, ticker in enumerate(tickers, 1):
        t_rows = 0
        for stmt in STATEMENTS:
            try:
                fs = src.get_financials(ticker, stmt, period="year")
                t_rows += store.store_statement(fs, max_periods=years, source=f"vnstock-{src.source}")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[{ticker}] {stmt} failed: {exc}")
        if t_rows == 0:
            failed.append(ticker)
        total_rows += t_rows
        logger.info(f"[{i}/{len(tickers)}] {ticker}: {t_rows} rows")

    print("\n" + "=" * 56)
    print(f"  VN30 FINANCIALS COLLECTED → DB ({store.backend})")
    print("=" * 56)
    print(f"  Tickers       : {len(tickers)} ({len(failed)} with no data: {failed})")
    print(f"  Rows written  : {total_rows}")
    print(f"  Rows in table : {store.count()}")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
