"""CLI to run backtest — supports all strategies including ensemble."""

import argparse
from pathlib import Path

import yaml
from loguru import logger

from data.feed import DataFeed
from backtest.engine import BacktestEngine
from risk.manager import RiskManager


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def create_strategy(name: str, config: dict, model_path: str = None):
    """Factory to create any registered strategy."""
    from strategies.rule_based.ema_trend import EMATrendStrategy
    from strategies.rule_based.monthly_breakout import MonthlyBreakoutStrategy
    from strategies.rule_based.grid_mean_reversion import GridMeanReversionStrategy
    from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy
    from strategies.ml_based import MLStrategy

    if name == "EMA-Trend":
        return EMATrendStrategy(params=config["strategies"]["registry"][0]["params"])
    elif name == "Monthly-Breakout":
        return MonthlyBreakoutStrategy(params=config["strategies"]["registry"][1]["params"])
    elif name == "Grid-MeanReversion":
        return GridMeanReversionStrategy(params={"grid_levels": 5, "lookback_days": 30, "atr_period": 14})
    elif name == "RegimeEnsemble":
        return RegimeEnsembleStrategy(params={
            "ema": config["strategies"]["registry"][0]["params"],
            "breakout": config["strategies"]["registry"][1]["params"],
            "grid": {"grid_levels": 5, "lookback_days": 30, "atr_period": 14},
            "regime_lookback": 30,
            "atr_period": 14,
        })
    elif name == "ML-Strategy":
        if model_path is None:
            # Try to load latest model by mtime
            import glob
            import os
            models = glob.glob("./ml/models/*.pkl")
            if not models:
                raise ValueError("No trained model found. Train a model first with: python -m ml.pipelines.train")
            model_path = max(models, key=os.path.getmtime)
        from ml.pipelines.xgboost_pipeline import MLClassifierPipeline
        pipeline = MLClassifierPipeline()
        pipeline.load(model_path)
        return MLStrategy(pipeline, name="ML-Strategy")
    else:
        raise ValueError(f"Unknown strategy: {name}")


def run_backtest(strategy_name: str, symbol: str, timeframe: str, config_path: str, model_path: str = None) -> dict:
    """Run a single backtest and return metrics."""
    config = load_config(config_path)

    feed = DataFeed(
        data_dir=config["data"]["data_dir"],
        exchange_id=config["data"]["exchange"],
    )
    df = feed.fetch(symbol, timeframe=timeframe, limit=2000)
    if df.empty:
        raise ValueError("No data available")

    strategy = create_strategy(strategy_name, config, model_path=model_path)
    risk = RiskManager(config["risk"])
    engine = BacktestEngine(
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"],
        slippage=config["backtest"]["slippage"],
    )
    result = engine.run(df, strategy, risk)

    metrics = {
        "strategy": strategy_name,
        "total_return": result.total_return,
        "sharpe": result.sharpe,
        "max_drawdown": result.max_drawdown,
        "winrate": result.winrate,
        "profit_factor": result.profit_factor,
        "total_trades": len(result.trades),
    }

    # Extra info for ensemble
    if hasattr(strategy, "regime_distribution"):
        metrics["regime_distribution"] = strategy.regime_distribution
    if hasattr(strategy, "last_signal_source"):
        metrics["last_signal_source"] = strategy.last_signal_source

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument("--strategy", default="RegimeEnsemble")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--config", default="config/system.yaml")
    parser.add_argument("--compare", action="store_true", help="Run all strategies and compare")
    args = parser.parse_args()

    if args.compare:
        strategies = ["EMA-Trend", "Monthly-Breakout", "Grid-MeanReversion", "RegimeEnsemble"]
        results = []
        for name in strategies:
            logger.info(f"Running {name}...")
            try:
                metrics = run_backtest(name, args.symbol, args.timeframe, args.config)
                results.append(metrics)
            except Exception as e:
                logger.error(f"{name} failed: {e}")

        # Print comparison table
        print("\n" + "=" * 90)
        print(f"{'Strategy':<22} {'Return':>8} {'Sharpe':>7} {'Max DD':>8} {'Winrate':>8} {'PF':>7} {'Trades':>7}")
        print("-" * 90)
        for r in results:
            print(
                f"{r['strategy']:<22} "
                f"{r['total_return']:>7.2%} "
                f"{r['sharpe']:>7.2f} "
                f"{r['max_drawdown']:>7.2%} "
                f"{r['winrate']:>7.2%} "
                f"{r['profit_factor']:>7.2f} "
                f"{r['total_trades']:>7d}"
            )
            if "regime_distribution" in r:
                rd = r["regime_distribution"]
                print(f"  → Regime: trending={rd.get('trending',0):.0%}, ranging={rd.get('ranging',0):.0%}, neutral={rd.get('neutral',0):.0%}")
        print("=" * 90 + "\n")
    else:
        metrics = run_backtest(args.strategy, args.symbol, args.timeframe, args.config)
        print("\n========== BACKTEST RESULT ==========")
        print(f"Strategy     : {metrics['strategy']}")
        print(f"Total Return : {metrics['total_return']:.2%}")
        print(f"Sharpe Ratio : {metrics['sharpe']:.2f}")
        print(f"Max Drawdown : {metrics['max_drawdown']:.2%}")
        print(f"Winrate      : {metrics['winrate']:.2%}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"Total Trades : {metrics['total_trades']}")
        if "regime_distribution" in metrics:
            rd = metrics["regime_distribution"]
            print(f"Regimes      : trending={rd.get('trending',0):.0%}, ranging={rd.get('ranging',0):.0%}, neutral={rd.get('neutral',0):.0%}")
        print("=====================================\n")


if __name__ == "__main__":
    main()
