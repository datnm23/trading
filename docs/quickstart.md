# Quick Start Guide

## 1. Backtest

```bash
# Single strategy
python -m backtest.run --strategy RegimeEnsemble --symbol BTC/USDT --timeframe 1d

# Compare all strategies
python -m backtest.run --compare
```

## 2. ML Pipeline

```bash
# Train XGBoost model (default)
python3 -m ml.pipelines.train --symbol BTC/USDT --timeframe 1d --model-type xgboost

# Train with hyperparameter tuning
python3 -m ml.pipelines.train --symbol BTC/USDT --timeframe 1d --model-type xgboost --n-iter 20

# Quick train/predict via Python
python3 -c "
from data.feed import DataFeed
from ml.pipelines.xgboost_pipeline import MLClassifierPipeline

feed = DataFeed()
df = feed.fetch('BTC/USDT', timeframe='1d', limit=1000)
pipeline = MLClassifierPipeline()
metrics = pipeline.train(df)
pipeline.save('./ml/models/latest_model.pkl')
print(f'Accuracy: {metrics[\"mean_accuracy\"]:.3f}')
"

# Predict
python3 -c "
from data.feed import DataFeed
from ml.pipelines.xgboost_pipeline import MLClassifierPipeline

feed = DataFeed()
df = feed.fetch('BTC/USDT', timeframe='1d', limit=100)
pipeline = MLClassifierPipeline()
pipeline.load('./ml/models/latest_model.pkl')
pred = pipeline.predict(df)
print(f'Signal: {pred[\"signal\"].iloc[-1]}')
"
```

## 3. Paper Trading

```bash
# Run paper trading bot (will check every 60s)
python3 -c "
from execution.paper_trading import PaperTradingEngine
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy
from risk.manager import RiskManager

strategy = RegimeEnsembleStrategy()
risk = RiskManager({'max_risk_per_trade': 0.01, 'max_total_exposure': 0.10, 'max_drawdown_pct': 0.15, 'position_sizing': 'atr_based'})
engine = PaperTradingEngine(strategy=strategy, risk_manager=risk, symbol='BTC/USDT', timeframe='1d')
engine.run(max_iterations=10)  # Run 10 cycles for demo
"
```

## 4. Order Manager

```python
from execution.order_manager import OrderManager, OrderSide, OrderType

# Paper mode
om = OrderManager(paper_mode=True)
order = om.create_order("BTC/USDT", OrderSide.BUY, amount=0.01, strategy_name="EMA-Trend")
result = om.submit(order, last_price=65000)
print(result.order.status)  # filled
print(om.get_summary())
```

## 5. Trade Journal

```python
from journal.trade_logger import TradeLogger, TradeRecord, JournalEntry

logger = TradeLogger()

# Log a completed trade
logger.log_trade(TradeRecord(
    symbol="BTC/USDT",
    strategy="EMA-Trend",
    side="long",
    entry_price=64000,
    exit_price=65000,
    size=0.01,
    pnl=100,
    pnl_pct=0.0156,
    exit_reason="take_profit",
    reasoning="EMA cross confirmed on 4h",
    emotion_before="calm",
    emotion_after="confident",
))

# Daily journal
logger.log_journal(JournalEntry(
    date="2026-04-21",
    entry_type="post_session",
    content="Followed plan strictly. No FOMO entries.",
    emotion="calm",
    focus_score=8,
    discipline_score=9,
))

# Summary
print(logger.trade_summary())
```

## 6. Streamlit Dashboard

```bash
streamlit run knowledge_engine/ui.py
```

Then open http://localhost:8501

### Dashboard pages:
- **Backtest**: Run and compare strategies
- **Wiki Chat**: Semantic search over 683 wiki concepts
- **Live Status**: Paper trading monitor (mock)
- **ML Models**: Train models and view feature importance
