"""Rolling retraining: train model on expanding window, evaluate on next month.

This avoids look-ahead bias by strictly training only on data available
before the prediction period.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
import pandas as pd
from loguru import logger

from data.feed import DataFeed
from ml.features.engineering import compute_features
from ml.features.selection import full_feature_selection, select_by_importance
from ml.pipelines.xgboost_pipeline import MLClassifierPipeline
from ml.models.registry import ModelRegistry, ModelRecord
from strategies.ml_based import MLStrategy
from backtest.engine import BacktestEngine
from risk.manager import RiskManager


class RollingRetrainer:
    """Train models on expanding window and evaluate forward."""

    def __init__(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        train_window_days: int = 730,  # 2 years training data
        retrain_interval_days: int = 30,  # Retrain every month
        model_type: str = "gradient_boosting",
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.train_window_days = train_window_days
        self.retrain_interval_days = retrain_interval_days
        self.model_type = model_type
        self.feed = DataFeed()
        self.registry = ModelRegistry()

    def run(self, start_date: str, end_date: str) -> List[dict]:
        """Run rolling retraining from start to end date.
        
        Returns list of period results.
        """
        # Load full history
        df = self.feed.fetch(self.symbol, timeframe=self.timeframe, limit=2000)
        if df.empty:
            raise ValueError("No data available")

        df.index = pd.to_datetime(df.index)
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        periods = []
        current = start

        while current < end:
            period_end = current + timedelta(days=self.retrain_interval_days)
            if period_end > end:
                period_end = end

            result = self._train_and_evaluate(df, current, period_end)
            periods.append(result)

            current = period_end

        return periods

    def _train_and_evaluate(self, df: pd.DataFrame, period_start: pd.Timestamp, period_end: pd.Timestamp) -> dict:
        """Train on data before period_start, evaluate on [period_start, period_end)."""
        train_cutoff = period_start
        train_start = train_cutoff - timedelta(days=self.train_window_days)

        train_mask = (df.index >= train_start) & (df.index < train_cutoff)
        test_mask = (df.index >= period_start) & (df.index < period_end)

        train_df = df[train_mask]
        test_df = df[test_mask]

        if len(train_df) < 100 or len(test_df) < 5:
            logger.warning(f"Insufficient data for period {period_start.date()} - {period_end.date()}")
            return {
                "period_start": period_start,
                "period_end": period_end,
                "train_size": len(train_df),
                "test_size": len(test_df),
                "skipped": True,
            }

        logger.info(f"Training {period_start.date()} | Train: {len(train_df)} bars | Test: {len(test_df)} bars")

        # Train model
        pipeline = MLClassifierPipeline()
        metrics = pipeline.train(train_df)

        # Backtest on test period (include last 100 bars of train for warmup)
        warmup_df = pd.concat([train_df.tail(100), test_df])
        strategy = MLStrategy(pipeline, name=f"ML-{period_start.strftime('%Y%m')}")
        risk = RiskManager({
            "max_risk_per_trade": 0.01,
            "max_total_exposure": 0.10,
            "max_drawdown_pct": 0.20,
            "position_sizing": "fixed_fractional",
        })
        engine = BacktestEngine(initial_capital=100000, commission=0.001, slippage=0.0005)
        result = engine.run(warmup_df, strategy, risk)

        # Save model
        model_name = f"rolling_{self.model_type}_{self.symbol.replace('/', '_')}_{period_start.strftime('%Y%m%d')}"
        model_path = f"./ml/models/{model_name}.pkl"
        pipeline.save(model_path)

        record = ModelRecord(
            name=model_name,
            model_type=self.model_type,
            symbol=self.symbol,
            timeframe=self.timeframe,
            features=len(pipeline.feature_names) if pipeline.feature_names else 0,
            accuracy=metrics["mean_accuracy"],
            precision=metrics["mean_precision"],
            recall=metrics["mean_recall"],
            f1=metrics["mean_f1"],
            best_params={},
            feature_importance={},
            created_at=datetime.now().isoformat(),
            path=model_path,
            notes=f"rolling_window={self.train_window_days}d, period={period_start.date()}-{period_end.date()}",
        )
        self.registry.register(record)

        return {
            "period_start": period_start,
            "period_end": period_end,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "test_return": result.total_return,
            "test_sharpe": result.sharpe,
            "test_max_dd": result.max_drawdown,
            "test_trades": len(result.trades),
            "model_accuracy": metrics["mean_accuracy"],
            "model_f1": metrics["mean_f1"],
            "skipped": False,
        }

    def summary(self, periods: List[dict]) -> pd.DataFrame:
        """Return summary of all periods."""
        valid = [p for p in periods if not p.get("skipped", False)]
        if not valid:
            return pd.DataFrame()

        df = pd.DataFrame(valid)
        df["period"] = df["period_start"].dt.strftime("%Y-%m")

        print("\n" + "=" * 80)
        print("ROLLING RETRAINING SUMMARY")
        print("=" * 80)
        print(f"Periods evaluated: {len(valid)}")
        print(f"Mean test return:  {df['test_return'].mean():.2%}")
        print(f"Mean Sharpe:       {df['test_sharpe'].mean():.2f}")
        print(f"Mean max DD:       {df['test_max_dd'].mean():.2%}")
        print(f"Mean trades/month: {df['test_trades'].mean():.1f}")
        print(f"Win months:        {(df['test_return'] > 0).sum()}/{len(valid)}")
        print("=" * 80 + "\n")

        return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--window", type=int, default=730)
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()

    trainer = RollingRetrainer(
        symbol=args.symbol,
        train_window_days=args.window,
        retrain_interval_days=args.interval,
    )
    periods = trainer.run(args.start, args.end)
    trainer.summary(periods)
