"""Collect VN30 financial statements (BS/IS/CF) → database.

Scope: VN30, last N periods. Source: vnstock free (VCI) — hard-capped at the
4 most-recent periods (covers 2 years annual OR 4 quarters).
Storage: PostgreSQL if TRADING_DB_URL reachable, else SQLite fallback.

Run: python3 scripts/collect_vn30_financials.py [periods] [year|quarter]
  e.g.  ... 2 year      -> last 2 fiscal years (default)
        ... 4 quarter   -> last 4 quarters
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Allow running as a script file (python3 scripts/...) — ensure project root is
# importable so `data.vn.*` resolves regardless of cwd / sys.path[0].
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from loguru import logger

from data.vn.universe import get_vn30
from data.vn.vnstock_source import VnstockSource
from data.vn.financials_store import FinancialsStore

STATEMENTS = ["balance_sheet", "income_statement", "cash_flow"]


def main() -> int:
    periods = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    period_type = sys.argv[2] if len(sys.argv) > 2 else "year"
    if period_type not in ("year", "quarter"):
        print(f"Invalid period_type {period_type!r}; use 'year' or 'quarter'")
        return 2
    tickers = get_vn30()
    # Throttle 5s to stay under vnstock guest limit (20 req/min); 30 tickers x 3
    # statements = 90 calls.
    src = VnstockSource(source="VCI", throttle_seconds=5.0)
    store = FinancialsStore()

    logger.info(f"Collecting {len(tickers)} VN30 tickers x {len(STATEMENTS)} statements, last {periods} {period_type}")
    total_rows = 0
    failed = []
    for i, ticker in enumerate(tickers, 1):
        t_rows = 0
        for stmt in STATEMENTS:
            try:
                fs = src.get_financials(ticker, stmt, period=period_type)
                t_rows += store.store_statement(fs, max_periods=periods, source=f"vnstock-{src.source}")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[{ticker}] {stmt} failed: {exc}")
        if t_rows == 0:
            failed.append(ticker)
        total_rows += t_rows
        logger.info(f"[{i}/{len(tickers)}] {ticker}: {t_rows} rows")

    # Authoritative shares-outstanding (issue_share) → vn_shares. Fixes the
    # derived-shares error (profit/eps ~2× off) that poisons Market Cap, P/B, DCF.
    logger.info("Collecting issue_share (shares outstanding) for VN30")
    shares_ok = 0
    for i, ticker in enumerate(tickers, 1):
        try:
            company = src.get_company(ticker)
            n = company.issue_share if company else 0.0
            if n and n > 0:
                store.set_shares(ticker, n, source=f"vnstock-{src.source}")
                shares_ok += 1
                logger.info(f"[{i}/{len(tickers)}] {ticker}: issue_share={n/1e9:.2f} tỷ cp")
            else:
                logger.warning(f"[{i}/{len(tickers)}] {ticker}: no issue_share")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{ticker}] issue_share failed: {exc}")

    print("\n" + "=" * 56)
    print(f"  VN30 FINANCIALS COLLECTED → DB ({store.backend})")
    print("=" * 56)
    print(f"  Tickers       : {len(tickers)} ({len(failed)} with no data: {failed})")
    print(f"  Rows written  : {total_rows}")
    print(f"  Rows in table : {store.count()}")
    print(f"  Shares (vn_shares): {shares_ok}/{len(tickers)} tickers")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
