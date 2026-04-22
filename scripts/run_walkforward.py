"""Run walk-forward blind test on historical data.

Trains on past data, tests on future unseen data.
Strategies: RegimeEnsemble (wiki+psych), ML-XGBoost, Buy&Hold
"""

import sys
sys.path.insert(0, "/home/datnm/projects/trading")

import argparse
import yaml
from pathlib import Path
from loguru import logger

import pandas as pd
import numpy as np

from data.feed import DataFeed
from backtest.walkforward import WalkForwardEngine
from backtest.engine import BacktestEngine
from risk.manager import RiskManager
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy
from strategies.benchmarks import BuyHoldStrategy
from strategies.ml_based import MLStrategy
from ml.pipelines.train import train_optimized


def load_config():
    with open("/home/datnm/projects/trading/config/system.yaml") as f:
        return yaml.safe_load(f)


def run_regime_ensemble_walkforward(df: pd.DataFrame, config: dict, label: str, train_bars: int = 180, test_bars: int = 90):
    """Run walk-forward for RegimeEnsemble with wiki + psych."""
    logger.info(f"\n{'='*80}\nRegimeEnsemble Walk-Forward ({label})\n{'='*80}")

    def make_strategy():
        return RegimeEnsembleStrategy(params=config["strategies"]["registry"][2]["params"])

    risk = RiskManager(config["risk"])
    engine = WalkForwardEngine(
        strategy_factory=make_strategy,
        risk_manager=risk,
        train_window_bars=train_bars,
        test_window_bars=test_bars,
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"],
        slippage=config["backtest"]["slippage"],
    )
    results = engine.run(df)

    # Save
    engine.save(f"/home/datnm/projects/trading/data/walkforward_regime_{label}.json")
    return results


def run_buyhold_walkforward(df: pd.DataFrame, config: dict, label: str, train_bars: int = 180, test_bars: int = 90):
    """Run walk-forward for Buy & Hold benchmark."""
    logger.info(f"\n{'='*80}\nBuy&Hold Walk-Forward ({label})\n{'='*80}")

    def make_strategy():
        return BuyHoldStrategy()

    risk = RiskManager(config["risk"])
    engine = WalkForwardEngine(
        strategy_factory=make_strategy,
        risk_manager=risk,
        train_window_bars=train_bars,
        test_window_bars=test_bars,
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"],
        slippage=config["backtest"]["slippage"],
    )
    results = engine.run(df)

    engine.save(f"/home/datnm/projects/trading/data/walkforward_buyhold_{label}.json")
    return results


def run_ml_walkforward(df: pd.DataFrame, config: dict, label: str, train_bars: int = 180, test_bars: int = 90):
    """Run walk-forward for ML-XGBoost with rolling retrain each period."""
    logger.info(f"\n{'='*80}\nML-XGBoost Walk-Forward ({label})\n{'='*80}")

    risk = RiskManager(config["risk"])
    train_window = train_bars
    test_window = test_bars
    initial_capital = config["backtest"]["initial_capital"]

    results = []
    total_bars = len(df)
    current = train_window

    while current + test_window <= total_bars:
        train_end = current
        train_start = max(0, train_end - train_window)
        test_end = min(current + test_window, total_bars)

        train_df = df.iloc[train_start:train_end]
        test_df = df.iloc[train_end:test_end]

        period_label = f"{df.index[train_end].strftime('%Y-%m-%d')}_{df.index[test_end-1].strftime('%Y-%m-%d')}"
        logger.info(f"ML Period {period_label} | Train: {len(train_df)} | Test: {len(test_df)}")

        # Train model on train data
        try:
            from ml.pipelines.xgboost_pipeline import MLClassifierPipeline
            # Step 1: Raise confidence threshold to 0.75 to filter noise
            pipeline = MLClassifierPipeline(n_splits=3, threshold=0.75)
            pipeline.train(train_df)

            # Save checkpoint
            checkpoint_dir = Path("/home/datnm/projects/trading/ml/models/walkforward")
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            cp_path = checkpoint_dir / f"xgb_v2_{label}_{period_label}.pkl"
            pipeline.save(str(cp_path))

            # Run strategy — prepend train tail so BacktestEngine's 100-bar
            # warmup doesn't swallow the entire test window.
            train_tail = train_df.iloc[-100:]
            combined = pd.concat([train_tail, test_df])

            # Step 1: Enable trend filter (only buy when ema20 >= ema50)
            strategy = MLStrategy(pipeline, name="ML-WF-v2", use_trend_filter=True)

            be = BacktestEngine(
                initial_capital=initial_capital,
                commission=config["backtest"]["commission"],
                slippage=config["backtest"]["slippage"],
            )
            risk.guard.reset()
            result = be.run(combined, strategy, risk)

            from backtest.walkforward import WalkForwardResult
            total_trades = len(result.trades)
            gross_return = result.total_return + (result.total_cost / initial_capital if initial_capital else 0)
            wf_result = WalkForwardResult(
                period_label=period_label,
                train_start=train_df.index[0],
                train_end=train_df.index[-1],
                test_start=test_df.index[0],
                test_end=test_df.index[-1],
                train_bars=len(train_df),
                test_bars=len(test_df),
                metrics={
                    "total_return": result.total_return,
                    "gross_return": gross_return,
                    "total_cost": result.total_cost,
                    "avg_cost_per_trade": result.total_cost / total_trades if total_trades else 0,
                    "sharpe": result.sharpe,
                    "max_drawdown": result.max_drawdown,
                    "winrate": result.winrate,
                    "profit_factor": result.profit_factor,
                    "total_trades": total_trades,
                },
                trades=[],
                equity_curve=result.equity_curve,
                model_checkpoint=str(cp_path),
            )
            results.append(wf_result)
        except Exception as e:
            logger.error(f"ML period {period_label} failed: {e}")

        current += test_window

    # Save aggregate
    import json
    data = {
        "meta": {"strategy": "ML-XGBoost", "label": label, "periods": len(results)},
        "periods": [
            {
                "period_label": r.period_label,
                "metrics": r.metrics,
                "model_checkpoint": r.model_checkpoint,
            }
            for r in results
        ],
        "aggregate": {
            "total_return": sum(r.metrics["total_return"] for r in results),
            "avg_sharpe": np.mean([r.metrics["sharpe"] for r in results]) if results else 0,
            "avg_max_dd": np.mean([r.metrics["max_drawdown"] for r in results]) if results else 0,
            "total_trades": sum(r.metrics["total_trades"] for r in results),
        },
    }
    with open(f"/home/datnm/projects/trading/data/walkforward_ml_v2_{label}.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

    return results


def compare_results(results_map: dict, label: str):
    """Print comparison table of all strategies."""
    print("\n" + "=" * 100)
    print(f"WALK-FORWARD COMPARISON ({label})")
    print("=" * 100)

    # Build summary
    summary_rows = []
    for strategy_name, results in results_map.items():
        if not results:
            continue
        total_return = sum(r.metrics["total_return"] for r in results)
        gross_return = sum(r.metrics.get("gross_return", r.metrics["total_return"]) for r in results)
        total_cost = sum(r.metrics.get("total_cost", 0) for r in results)
        total_trades = sum(r.metrics["total_trades"] for r in results)
        avg_cost = total_cost / total_trades if total_trades else 0
        avg_sharpe = np.mean([r.metrics["sharpe"] for r in results])
        avg_max_dd = np.mean([r.metrics["max_drawdown"] for r in results])
        win_months = sum(1 for r in results if r.metrics["total_return"] > 0)
        summary_rows.append({
            "Strategy": strategy_name,
            "Net Return": total_return,
            "Gross Return": gross_return,
            "Total Cost": total_cost,
            "Avg Cost/Trade": avg_cost,
            "Avg Sharpe": avg_sharpe,
            "Avg Max DD": avg_max_dd,
            "Total Trades": total_trades,
            "Win Periods": f"{win_months}/{len(results)}",
        })

    df = pd.DataFrame(summary_rows)
    print(df.to_string(index=False))

    # Save report
    report_path = f"/home/datnm/projects/trading/docs/walkforward_report_{label}.md"
    with open(report_path, "w") as f:
        f.write(f"# Walk-Forward Blind Test Report ({label})\n\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n\n")
        f.write("## Aggregate Comparison\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n\n## Per-Period Breakdown\n\n")

        for strategy_name, results in results_map.items():
            f.write(f"### {strategy_name}\n\n")
            rows = []
            for r in results:
                rows.append({
                    "Period": r.period_label,
                    "Net Return": f"{r.metrics['total_return']:.2%}",
                    "Gross Return": f"{r.metrics.get('gross_return', r.metrics['total_return']):.2%}",
                    "Total Cost": f"{r.metrics.get('total_cost', 0):,.2f}",
                    "Avg Cost/Trade": f"{r.metrics.get('avg_cost_per_trade', 0):,.2f}",
                    "Sharpe": f"{r.metrics['sharpe']:.2f}",
                    "Max DD": f"{r.metrics['max_drawdown']:.2%}",
                    "Trades": r.metrics["total_trades"],
                })
            pdf = pd.DataFrame(rows)
            f.write(pdf.to_markdown(index=False))
            f.write("\n\n")

    print(f"\nReport saved to {report_path}")
    print("=" * 100)


def _bars_for_timeframe(tf: str, months_train: int = 6, months_test: int = 3):
    """Convert month windows to bar counts based on timeframe."""
    bars_per_day = {"1d": 1, "4h": 6, "1h": 24, "15m": 96}
    bpd = bars_per_day.get(tf, 1)
    train_bars = months_train * 30 * bpd
    test_bars = months_test * 30 * bpd
    return train_bars, test_bars


def main():
    parser = argparse.ArgumentParser(description="Walk-forward blind test")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--skip-ml", action="store_true", help="Skip ML training (faster)")
    args = parser.parse_args()

    config = load_config()
    label = f"{args.symbol.replace('/', '_')}_{args.timeframe}"

    # Compute bar windows
    train_bars, test_bars = _bars_for_timeframe(args.timeframe)

    # Fetch data (use larger limit for finer timeframes; cache will be used if present)
    fetch_limit = 1500 if args.timeframe == "1d" else 10000
    feed = DataFeed()
    df = feed.fetch(args.symbol, timeframe=args.timeframe, limit=fetch_limit, use_cache=True)
    if df.empty:
        raise ValueError("No data available")

    print(f"\nData loaded: {args.symbol} {args.timeframe} | {len(df)} bars | {df.index[0]} to {df.index[-1]}")
    print(f"Walk-forward windows: train={train_bars} bars | test={test_bars} bars")

    results_map = {}

    # 1. RegimeEnsemble
    results_map["RegimeEnsemble"] = run_regime_ensemble_walkforward(df, config, label, train_bars, test_bars)

    # 2. Buy&Hold
    results_map["BuyHold"] = run_buyhold_walkforward(df, config, label, train_bars, test_bars)

    # 3. ML-XGBoost v2 (threshold 0.75 + trend filter + cost-aware weights)
    if not args.skip_ml:
        results_map["ML-XGBoost-v2"] = run_ml_walkforward(df, config, label, train_bars, test_bars)

    # Compare
    compare_results(results_map, label)


if __name__ == "__main__":
    main()
