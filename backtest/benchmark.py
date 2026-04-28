"""Multi-symbol, multi-timeframe benchmark for wiki + psych impact.

Tests RegimeEnsemble strategy across:
    - Symbols: BTC/USDT, ETH/USDT, SOL/USDT
    - Timeframes: 1d, 4h, 1h
    - Modes: base (no wiki/psych) vs enhanced (wiki + psych)

Outputs:
    - Console comparison table
    - JSON results file for further analysis
"""

import json
import time
from pathlib import Path

import pandas as pd
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

import sys

sys.path.insert(0, "/home/datnm/projects/trading")

from backtest.engine import BacktestEngine
from backtest.enhanced_engine import EnhancedBacktestEngine, EnhancedBacktestResult
from data.feed import DataFeed
from risk.manager import RiskManager
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy


def load_config():
    import yaml

    with open("/home/datnm/projects/trading/config/system.yaml") as f:
        return yaml.safe_load(f)


def run_single_benchmark(
    symbol: str, timeframe: str, use_wiki: bool, use_psych: bool, config: dict
):
    """Run one backtest and return metrics."""
    feed = DataFeed()
    df = feed.fetch(symbol, timeframe=timeframe, limit=2000)
    if df.empty or len(df) < 150:
        return None

    strategy = RegimeEnsembleStrategy(
        params={
            "ema": config["strategies"]["registry"][0]["params"],
            "breakout": config["strategies"]["registry"][1]["params"],
            "grid": {"grid_levels": 5, "lookback_days": 30, "atr_period": 14},
            "regime_lookback": 30,
            "atr_period": 14,
            "wiki_min_alignment": 0.3,
        }
    )

    risk = RiskManager(config["risk"])

    if use_wiki or use_psych:
        engine = EnhancedBacktestEngine(
            initial_capital=config["backtest"]["initial_capital"],
            commission=config["backtest"]["commission"],
            slippage=config["backtest"]["slippage"],
            use_wiki=use_wiki,
            use_psych=use_psych,
            wiki_min_align=0.3,
            psych_config=config.get("psychology", {}),
        )
    else:
        engine = BacktestEngine(
            initial_capital=config["backtest"]["initial_capital"],
            commission=config["backtest"]["commission"],
            slippage=config["backtest"]["slippage"],
        )

    result = engine.run(df.copy(), strategy, risk)

    metrics = {
        "symbol": symbol,
        "timeframe": timeframe,
        "mode": "enhanced" if (use_wiki or use_psych) else "base",
        "wiki": use_wiki,
        "psych": use_psych,
        "total_return": result.total_return,
        "sharpe": result.sharpe,
        "max_drawdown": result.max_drawdown,
        "winrate": result.winrate,
        "profit_factor": result.profit_factor,
        "total_trades": len(result.trades),
        "bars": len(df),
    }

    # Add enhanced-specific stats
    if isinstance(result, EnhancedBacktestResult):
        metrics["wiki_blocked"] = result.wiki_blocked
        metrics["wiki_downgraded"] = result.wiki_downgraded
        metrics["wiki_avg_alignment"] = result.wiki_avg_alignment
        metrics["psych_paused_bars"] = result.psych_paused_bars
        metrics["psych_size_reductions"] = result.psych_size_reductions

    return metrics


def run_full_benchmark():
    config = load_config()

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    timeframes = ["1d", "4h"]

    results = []

    print("\n" + "=" * 100)
    print("MULTI-SYMBOL/TIMEFRAME BENCHMARK")
    print("=" * 100)
    print(f"Symbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print("Strategies: RegimeEnsemble")
    print("=" * 100)

    for symbol in symbols:
        for tf in timeframes:
            print(f"\n--- {symbol} @ {tf} ---")

            # Base
            print("  Running BASE...", end=" ")
            start = time.time()
            base = run_single_benchmark(symbol, tf, False, False, config)
            elapsed = time.time() - start
            if base:
                print(
                    f"Done in {elapsed:.1f}s | Return: {base['total_return']:.2%} | Trades: {base['total_trades']}"
                )
                results.append(base)
            else:
                print("SKIPPED (no data)")
                continue

            # Enhanced (wiki only)
            print("  Running WIKI...", end=" ")
            start = time.time()
            wiki = run_single_benchmark(symbol, tf, True, False, config)
            elapsed = time.time() - start
            if wiki:
                print(
                    f"Done in {elapsed:.1f}s | Return: {wiki['total_return']:.2%} | "
                    f"Trades: {wiki['total_trades']} | Downgraded: {wiki.get('wiki_downgraded', 0)}"
                )
                results.append(wiki)

            # Enhanced (wiki + psych)
            print("  Running WIKI+PSYCH...", end=" ")
            start = time.time()
            both = run_single_benchmark(symbol, tf, True, True, config)
            elapsed = time.time() - start
            if both:
                print(
                    f"Done in {elapsed:.1f}s | Return: {both['total_return']:.2%} | "
                    f"Trades: {both['total_trades']} | Downgraded: {both.get('wiki_downgraded', 0)} | "
                    f"PsychPauses: {both.get('psych_paused_bars', 0)}"
                )
                results.append(both)

    # Print summary tables
    print_summary(results)

    # Save results
    output_path = Path("/home/datnm/projects/trading/data/benchmark_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")

    return results


def print_summary(results):
    """Print formatted comparison tables."""
    # ruff: noqa: E402
    df = pd.DataFrame(results)
    if df.empty:
        print("No results to display.")
        return

    print("\n" + "=" * 120)
    print("DETAILED RESULTS")
    print("=" * 120)
    print(
        f"{'Symbol':<12} {'TF':<4} {'Mode':<10} {'Return':>8} {'Sharpe':>7} "
        f"{'MaxDD':>8} {'Win%':>7} {'PF':>6} {'Trades':>6} {'Wiki↓':>6} {'Psych⏸':>6}"
    )
    print("-" * 120)

    for _, r in df.iterrows():
        mode_str = r["mode"]
        if r.get("wiki") and r.get("psych"):
            mode_str = "wiki+psych"
        elif r.get("wiki"):
            mode_str = "wiki"

        print(
            f"{r['symbol']:<12} {r['timeframe']:<4} {mode_str:<10} "
            f"{r['total_return']:>7.2%} {r['sharpe']:>7.2f} {r['max_drawdown']:>7.2%} "
            f"{r['winrate']:>6.1%} {r['profit_factor']:>6.2f} {r['total_trades']:>6d} "
            f"{int(r.get('wiki_downgraded', 0)):>6d} {int(r.get('psych_paused_bars', 0)):>6d}"
        )

    # Comparison by symbol/timeframe
    print("\n" + "=" * 120)
    print("IMPACT ANALYSIS (Enhanced vs Base)")
    print("=" * 120)
    print(
        f"{'Symbol':<12} {'TF':<4} {'ΔReturn':>10} {'ΔSharpe':>9} {'ΔMaxDD':>9} "
        f"{'ΔTrades':>9} {'WikiBlocked':>12} {'WikiDowngrade':>14}"
    )
    print("-" * 120)

    for symbol in df["symbol"].unique():
        for tf in df["timeframe"].unique():
            base = df[
                (df["symbol"] == symbol)
                & (df["timeframe"] == tf)
                & (df["mode"] == "base")
            ]
            enhanced = df[
                (df["symbol"] == symbol)
                & (df["timeframe"] == tf)
                & (df["wiki"])
                & (df["psych"])
            ]

            if base.empty or enhanced.empty:
                continue

            b = base.iloc[0]
            e = enhanced.iloc[0]

            print(
                f"{symbol:<12} {tf:<4} "
                f"{e['total_return'] - b['total_return']:>+9.2%} "
                f"{e['sharpe'] - b['sharpe']:>+9.2f} "
                f"{e['max_drawdown'] - b['max_drawdown']:>+9.2%} "
                f"{e['total_trades'] - b['total_trades']:>+9d} "
                f"{int(e.get('wiki_blocked', 0)):>12d} "
                f"{int(e.get('wiki_downgraded', 0)):>14d}"
            )

    # Aggregate stats
    print("\n" + "=" * 120)
    print("AGGREGATE STATISTICS")
    print("=" * 120)

    base_df = df[df["mode"] == "base"]
    enhanced_df = df[(df["wiki"]) & (df["psych"])]

    if not base_df.empty and not enhanced_df.empty:
        print(
            f"{'Metric':<25} {'Base Avg':>12} {'Enhanced Avg':>14} {'Improvement':>12}"
        )
        print("-" * 65)

        for metric in [
            "total_return",
            "sharpe",
            "max_drawdown",
            "winrate",
            "profit_factor",
        ]:
            base_avg = base_df[metric].mean()
            enh_avg = enhanced_df[metric].mean()
            delta = enh_avg - base_avg
            print(f"{metric:<25} {base_avg:>12.4f} {enh_avg:>14.4f} {delta:>+12.4f}")

    print("=" * 120)


if __name__ == "__main__":
    run_full_benchmark()
