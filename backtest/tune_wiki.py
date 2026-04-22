"""Wiki threshold tuning benchmark.

Tests multiple wiki_min_alignment values to find optimal threshold
that blocks bad signals without filtering out good ones.

Thresholds tested: 0.30, 0.25, 0.20, 0.15, 0.10
"""

import sys
sys.path.insert(0, "/home/datnm/projects/trading")

import json
import time
from pathlib import Path

import pandas as pd
from loguru import logger
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="WARNING")  # Quieter

import yaml
from data.feed import DataFeed
from backtest.enhanced_engine import EnhancedBacktestEngine
from risk.manager import RiskManager
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy


def load_config():
    with open("/home/datnm/projects/trading/config/system.yaml") as f:
        return yaml.safe_load(f)


def run_with_threshold(symbol: str, timeframe: str, threshold: float, config: dict):
    """Run single backtest with specific wiki threshold."""
    feed = DataFeed()
    df = feed.fetch(symbol, timeframe=timeframe, limit=2000)
    if df.empty or len(df) < 150:
        return None

    strategy = RegimeEnsembleStrategy(params={
        "ema": config["strategies"]["registry"][0]["params"],
        "breakout": config["strategies"]["registry"][1]["params"],
        "grid": {"grid_levels": 5, "lookback_days": 30, "atr_period": 14},
        "regime_lookback": 30,
        "atr_period": 14,
        "wiki_min_alignment": threshold,
    })

    risk = RiskManager(config["risk"])

    engine = EnhancedBacktestEngine(
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"],
        slippage=config["backtest"]["slippage"],
        use_wiki=True,
        use_psych=True,
        wiki_min_align=threshold,
        psych_config=config.get("psychology", {}),
    )

    result = engine.run(df.copy(), strategy, risk)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "wiki_threshold": threshold,
        "total_return": result.total_return,
        "sharpe": result.sharpe,
        "max_drawdown": result.max_drawdown,
        "winrate": result.winrate,
        "profit_factor": result.profit_factor,
        "total_trades": len(result.trades),
        "wiki_blocked": result.wiki_blocked,
        "wiki_downgraded": result.wiki_downgraded,
        "wiki_avg_alignment": result.wiki_avg_alignment,
        "psych_paused_bars": result.psych_paused_bars,
        "psych_size_reductions": result.psych_size_reductions,
    }


def run_threshold_sweep():
    config = load_config()

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    timeframes = ["1d", "4h"]
    thresholds = [0.30, 0.25, 0.20, 0.15, 0.10]

    results = []

    print("=" * 100)
    print("WIKI THRESHOLD TUNING BENCHMARK")
    print("=" * 100)
    print(f"Symbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print(f"Thresholds: {thresholds}")
    print("=" * 100)

    total_runs = len(symbols) * len(timeframes) * len(thresholds)
    run_count = 0

    for symbol in symbols:
        for tf in timeframes:
            print(f"\n--- {symbol} @ {tf} ---")
            for thresh in thresholds:
                run_count += 1
                print(f"  [{run_count}/{total_runs}] threshold={thresh:.2f}... ", end="", flush=True)
                start = time.time()
                r = run_with_threshold(symbol, tf, thresh, config)
                elapsed = time.time() - start
                if r:
                    print(
                        f"Return={r['total_return']:+.2%} | "
                        f"Trades={r['total_trades']} | "
                        f"Blocked={r['wiki_blocked']} | "
                        f"Downgraded={r['wiki_downgraded']} | "
                        f"AvgAlign={r['wiki_avg_alignment']:.3f} | "
                        f"({elapsed:.1f}s)"
                    )
                    results.append(r)
                else:
                    print("SKIPPED")

    # Save
    output = Path("/home/datnm/projects/trading/data/wiki_threshold_results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print_summary(results)
    return results


def print_summary(results):
    df = pd.DataFrame(results)
    if df.empty:
        return

    print("\n" + "=" * 120)
    print("DETAILED RESULTS BY THRESHOLD")
    print("=" * 120)
    print(f"{'Symbol':<12} {'TF':<4} {'Thresh':<6} {'Return':>8} {'Sharpe':>7} {'MaxDD':>8} {'Win%':>7} {'PF':>6} {'Trades':>6} {'Blocked':>7} {'Downgraded':>10} {'AvgAlign':>8}")
    print("-" * 120)

    for _, r in df.sort_values(["symbol", "timeframe", "wiki_threshold"]).iterrows():
        print(
            f"{r['symbol']:<12} {r['timeframe']:<4} {r['wiki_threshold']:<6.2f} "
            f"{r['total_return']:>7.2%} {r['sharpe']:>7.2f} {r['max_drawdown']:>7.2%} "
            f"{r['winrate']:>6.1%} {r['profit_factor']:>6.2f} {r['total_trades']:>6d} "
            f"{r['wiki_blocked']:>7d} {r['wiki_downgraded']:>10d} {r['wiki_avg_alignment']:>8.3f}"
        )

    # Find best threshold per symbol/timeframe
    print("\n" + "=" * 120)
    print("OPTIMAL THRESHOLD PER CONFIGURATION (best Sharpe)")
    print("=" * 120)
    print(f"{'Symbol':<12} {'TF':<4} {'BestThresh':>10} {'Return':>8} {'Sharpe':>7} {'MaxDD':>8} {'Trades':>6} {'Blocked':>7}")
    print("-" * 120)

    for symbol in df["symbol"].unique():
        for tf in df["timeframe"].unique():
            subset = df[(df["symbol"] == symbol) & (df["timeframe"] == tf)]
            if subset.empty:
                continue
            best = subset.loc[subset["sharpe"].idxmax()]
            print(
                f"{symbol:<12} {tf:<4} {best['wiki_threshold']:>10.2f} "
                f"{best['total_return']:>7.2%} {best['sharpe']:>7.2f} {best['max_drawdown']:>7.2%} "
                f"{best['total_trades']:>6d} {best['wiki_blocked']:>7d}"
            )

    # Aggregate by threshold
    print("\n" + "=" * 120)
    print("AGGREGATE BY THRESHOLD")
    print("=" * 120)
    print(f"{'Threshold':<10} {'AvgReturn':>10} {'AvgSharpe':>10} {'AvgMaxDD':>10} {'AvgTrades':>10} {'TotalBlocked':>12} {'TotalDowngraded':>15}")
    print("-" * 120)

    for thresh in sorted(df["wiki_threshold"].unique()):
        subset = df[df["wiki_threshold"] == thresh]
        print(
            f"{thresh:<10.2f} {subset['total_return'].mean():>9.2%} {subset['sharpe'].mean():>10.2f} "
            f"{subset['max_drawdown'].mean():>10.2%} {subset['total_trades'].mean():>10.1f} "
            f"{subset['wiki_blocked'].sum():>12d} {subset['wiki_downgraded'].sum():>15d}"
        )

    # Recommendation
    print("\n" + "=" * 120)
    print("RECOMMENDATION")
    print("=" * 120)

    by_thresh = df.groupby("wiki_threshold").agg({
        "total_return": "mean",
        "sharpe": "mean",
        "max_drawdown": "mean",
        "wiki_blocked": "sum",
    }).reset_index()

    # Score: higher return, higher sharpe, less negative DD, but not too many blocks
    by_thresh["score"] = (
        by_thresh["total_return"] * 2 +
        by_thresh["sharpe"] * 0.5 +
        by_thresh["max_drawdown"] * 1.5  # max_drawdown is negative, so less negative = better
    )
    best = by_thresh.loc[by_thresh["score"].idxmax()]

    print(f"\nBased on aggregate performance (return, sharpe, drawdown):")
    print(f"  Recommended wiki_min_alignment: {best['wiki_threshold']:.2f}")
    print(f"  Expected avg return: {best['total_return']:.2%}")
    print(f"  Expected avg sharpe: {best['sharpe']:.2f}")
    print(f"  Expected avg max DD: {best['max_drawdown']:.2%}")
    print(f"  Total signals blocked: {int(best['wiki_blocked'])}")

    print("\n" + "=" * 120)


if __name__ == "__main__":
    run_threshold_sweep()
