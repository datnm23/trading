"""Quick integration test: MLStrategy + LiveTradingEngine."""

import os
import sys

sys.path.insert(0, "/home/datnm/projects/trading")

import pytest

# Skip entire module if DB not reachable
_db_url = os.environ.get("TRADING_DB_URL", "")
_db_reachable = False
if _db_url:
    try:
        import psycopg2
        conn = psycopg2.connect(_db_url, connect_timeout=3)
        conn.close()
        _db_reachable = True
    except Exception:
        pass
if not _db_reachable:
    pytest.skip("PostgreSQL not reachable — skipping DB-dependent integration test", allow_module_level=True)

import tempfile
import pandas as pd
import numpy as np

from strategies.ml_based import MLStrategy
from ml.pipelines.xgboost_pipeline import MLClassifierPipeline
from execution.live_trading import LiveTradingEngine
from risk.manager import RiskManager
import yaml

# Create minimal config
config = {
    "system": {"mode": "paper"},
    "data": {"symbols": ["BTC/USDT"], "timeframe": "1d"},
    "risk": {
        "max_risk_per_trade": 0.01,
        "max_total_exposure": 0.10,
        "max_drawdown_pct": 0.20,
        "position_sizing": "fixed_fractional",
    },
    "backtest": {"initial_capital": 100000},
    "execution": {"paper": True, "exchange_id": "binance", "testnet": True},
    "journal": {"db_url": os.environ.get("TRADING_DB_URL", "")},
    "monitoring": {"health_port": 18080, "alert_telegram": False},
    "psychology": {},
}

# Create synthetic data
np.random.seed(0)
n = 300
dates = pd.date_range(end="2026-04-21", periods=n, freq="D")
df = pd.DataFrame({
    "open": np.cumsum(np.random.randn(n)) + 50000,
    "high": np.cumsum(np.random.randn(n)) + 50100,
    "low": np.cumsum(np.random.randn(n)) + 49900,
    "close": np.cumsum(np.random.randn(n)) + 50000,
    "volume": np.random.randint(1000, 10000, n),
}, index=dates)
df["high"] = df[["open", "close", "high"]].max(axis=1)
df["low"] = df[["open", "close", "low"]].min(axis=1)

# Train a tiny model
pipeline = MLClassifierPipeline(n_splits=2, threshold=0.5)
metrics = pipeline.train(df)
print(f"Model trained | Accuracy: {metrics['mean_accuracy']:.3f}")

# Create ML strategy
strategy = MLStrategy(pipeline, name="ML-Test", use_trend_filter=False)

# Create LiveTradingEngine
engine = LiveTradingEngine(
    config=config,
    strategy=strategy,
    mode="paper",
    symbols=["BTC/USDT"],
)

print(f"Engine created | Paper mode: {engine.paper_mode}")
print(f"Strategy: {engine.strategy.__class__.__name__}")
print(f"Risk manager: {engine.risk.__class__.__name__}")

# Verify that the engine can process a bar without crashing
from strategies.base import StrategyContext
context = StrategyContext(
    symbol="BTC/USDT",
    bar=df.iloc[-1],
    history=df,
    account={"capital": engine.capital, "equity": engine.equity},
    positions=list(engine.positions.values()),
)
signal = strategy.on_bar(context)
print(f"Signal from ML strategy: {signal}")

# Verify health status retrieval (thread-safe)
status = engine.get_status()
print(f"Health status keys: {list(status.keys())}")
print("ML-Strategy + LiveTradingEngine integration OK")
