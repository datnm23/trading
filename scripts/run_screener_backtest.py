"""Live screener backtest runner (P6 validation) — VN30 vs VNINDEX.

Wraps the live VnstockSource in CachedDataSource so each ticker's OHLCV/financials
are fetched once (vnstock rate limit ~20 req/min, throttle 3.5s). Runs the
point-in-time rebalance backtest and writes a markdown report.

Chạy: python3 scripts/run_screener_backtest.py [report_path]
"""
from __future__ import annotations

import sys
import time
import warnings

warnings.filterwarnings("ignore")

from loguru import logger

from data.vn import build_default_source
from backtest.screener_backtest import (
    load_backtest_config,
    run_screener_backtest,
    write_backtest_report,
)

DEFAULT_REPORT = "plans/260615-1352-vn-stock-advisory-mvp1/research/screener-backtest-report.md"


def main() -> int:
    report_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPORT

    config = load_backtest_config("config/backtest.yaml")
    logger.info(f"Config: {config.get('start_date')}→{config.get('end_date')} "
                f"freq={config.get('rebalance_freq')} top_n={config.get('top_n')}")

    # Canonical hybrid source: DNSE adjusted OHLCV (no rate-limit) + vnstock
    # fundamentals (throttled 5s). Fresh cache dir so stale vnstock UNADJUSTED
    # OHLCV (which caused the −91% bug) is not reused.
    source = build_default_source(cache_dir="./data/vn_cache_dnse")

    t0 = time.time()
    try:
        result = run_screener_backtest(source, config)
    except Exception as exc:  # noqa: BLE001 — surface clearly, don't crash silently
        logger.error(f"Backtest FAILED: {exc!r}")
        return 1
    elapsed = time.time() - t0

    write_backtest_report(result, report_path)

    print("\n" + "=" * 60)
    print("  SCREENER BACKTEST — KẾT QUẢ (VN30 vs VNINDEX)")
    print("=" * 60)
    print(f"  Period          : {config.get('start_date')} → {config.get('end_date')}")
    print(f"  Rebalances      : {len(result.rebalance_records)} ({config.get('rebalance_freq')})")
    print(f"  Total return    : {result.total_return:+.2%}")
    print(f"  Benchmark return: {result.benchmark_return:+.2%}")
    print(f"  Alpha           : {result.alpha:+.2%}")
    print(f"  CAGR            : {result.cagr:+.2%}")
    print(f"  Max drawdown    : {result.max_drawdown:.2%}")
    print(f"  Sharpe          : {result.sharpe:.2f}")
    print(f"  Hit rate        : {result.hit_rate:.0%} kỳ thắng benchmark")
    print(f"  Fee drag        : {result.total_fees_paid:.2%}")
    print(f"  EDGE            : {'YES — vượt VNINDEX' if result.alpha > 0 else 'NO — thua benchmark'}")
    print(f"  Elapsed         : {elapsed:.0f}s")
    print(f"  Report          : {report_path}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
