# Quick Start Guide

## 1. Setup (Docker Compose — Khuyến nghị)

```bash
# 1. Config env
cp .env.example .env
# Edit .env nếu cần (API keys, Telegram tokens)

# 2. Start toàn bộ stack
docker compose up -d

# 3. Verify
docker compose ps
```

> **Lưu ý**: Stack chạy local với PostgreSQL, testnet, 4h timeframe. Truy cập Grafana tại http://localhost:3000 (admin/changeme).

### Hoặc chạy Python local (không Docker)

```bash
# 1. Install dependencies (trong virtual environment)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Start PostgreSQL
docker run -d --name trading-postgres \
  -e POSTGRES_USER=trader -e POSTGRES_PASSWORD=trading123 \
  -e POSTGRES_DB=trading_journal -p 5432:5432 \
  postgres:16-alpine

# 3. Copy và chỉnh sửa config
cp config/system.yaml config/local.yaml
# Edit API keys, symbols, risk params trong config/local.yaml
```

## 2. Chạy Tests

```bash
# Chạy toàn bộ test suite
pytest tests/ -v

# Chạy từng module
pytest tests/test_risk.py -v
pytest tests/test_execution.py -v
pytest tests/test_psychology.py -v
pytest tests/test_backend_api.py -v
pytest tests/test_ml_integration.py -v
```

## 3. Backtest

```bash
# Single strategy
python -m backtest.run --strategy RegimeEnsemble --symbol BTC/USDT --timeframe 1d

# Compare all strategies
python -m backtest.run --compare

# Walk-forward analysis
python -m backtest.walkforward --strategy RegimeEnsemble --symbol BTC/USDT --timeframe 4h
```

## 4. ML Pipeline

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

## 5. Paper Trading

```bash
# Run paper trading bot (kiểm tra mỗi 60s)
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

### Live Trading (Production)

```bash
# Paper mode (default)
python -m execution.live_trading --config config/local.yaml --mode paper --symbol BTC/USDT

# Live mode (requires graduation gate)
python -m execution.live_trading --config config/local.yaml --mode live --symbol BTC/USDT
```

## 6. Backend API

```bash
# Start FastAPI gateway
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --reload
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/strategies` | GET | List active strategies |
| `/api/v1/state` | GET | Full system state |
| `/api/v1/rebalance` | POST | Update allocation targets |
| `/api/v1/market/ohlcv` | GET | OHLCV candles |
| `/api/v1/market/tickers` | GET | Current prices |
| `/socket.io` | WS | Real-time updates |

```bash
# Test API
curl http://localhost:8090/health
curl "http://localhost:8090/api/v1/market/ohlcv?symbol=BTC/USDT&timeframe=1d&limit=5"
```

## 7. Order Manager

```python
from execution.order_manager import OrderManager, OrderSide, OrderType

# Paper mode
om = OrderManager(paper_mode=True)
order = om.create_order("BTC/USDT", OrderSide.BUY, amount=0.01, strategy_name="EMA-Trend")
result = om.submit(order, last_price=65000)
print(result.order.status)  # filled
print(om.get_summary())
```

## 8. Trade Journal

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

# Export
logger.export_trades_csv("./data/trades_export.csv")
logger.export_journal_json("./data/journal_export.json")
```

## 9. Streamlit Dashboard

```bash
streamlit run knowledge_engine/ui.py
```

Then open http://localhost:8501

### Dashboard pages:
- **Backtest**: Run and compare strategies
- **Wiki Chat**: Semantic search over 683 wiki concepts
- **Live Status**: Paper trading monitor
- **ML Models**: Train models and view feature importance

## 10. Health Monitoring

```bash
# Health check
curl http://localhost:8080/health
curl http://localhost:8080/metrics

# View in browser
# http://localhost:8080/health → JSON status
# http://localhost:8080/metrics → Plain text metrics
```

## 11. Wiki Knowledge Chat

```python
from knowledge_engine.rag import WikiRAG

rag = WikiRAG()
rag.query("Khi nào nên dùng trend following thay vì mean reversion?")
# → Trả lợi dựa trên concepts từ wiki
```

## 12. Common Commands

```bash
# Run all strategies comparison
python -m scripts.run_all_strategies

# Run walk-forward test
python -m scripts.run_walkforward --strategy RegimeEnsemble

# Query journal
python -m scripts.query_journal --summary

# Download full 4h data
python -m scripts.download_full_4h

# Lint code
ruff check .
ruff check . --fix
```
