# Hybrid Trading System — Kiến trúc

## Triết lý nền tảng (từ Turtle Trading Wiki)

Hệ thống được xây dựng dựa trên **3 tầng kiến trúc**:

1. **Tầng Kiến trúc (Logic)** — Edge, chiến lược, mô hình, dữ liệu
2. **Tầng Quản trị Rủi ro** — Position sizing, stop-loss, drawdown control
3. **Tầng Thực thi & Tâm lý** — Auto-execution, journaling, kỷ luật hệ thống

> "Nhiều ngườichỉ tối ưu tầng thi công (entry/indicator) trong khi bỏ qua tầng kiến trúc (bản chất edge và điều kiện sống còn)."

## Kiến trúc Tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                     │
│  Dashboard | Charts | Position Monitor | Rebalance UI       │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND API (FastAPI)                        │
│  REST + Socket.IO | StateAggregator | MarketDataProvider    │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE ENGINE                          │
│  (RAG + LLM + Wiki Anchor → Context-aware decisions)        │
│  683 concepts | Signal Validator | Wiki Feedback Loop       │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   STRATEGY LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Rule-Based  │  │ ML Models   │  │ Ensemble / Selector │ │
│  │ (EMA-Trend, │  │ (XGBoost,   │  │ (RegimeEnsemble:    │ │
│  │  Monthly    │  │  MLStrategy)│  │  Wiki + Psychology) │ │
│  │  Breakout,  │  │             │  │                     │ │
│  │  Grid)      │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   RISK MANAGEMENT LAYER                      │
│  Position Sizing │ Stop Loss │ Max Drawdown │ Correlation   │
│  Trailing Stop   │ Partial Exit │ Psychology Enforcer     │
│  Regime-Aware Risk (bull/bear/sideways multipliers)         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER                            │
│  Paper Trading → Live Trading (Binance via CCXT)            │
│  Order Manager | Retry Logic | Slippage Tracker             │
│  Graduation Gate (paper → live safety criteria)             │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              MONITORING & JOURNALING                         │
│  Telegram Alerts | Health Server | Daily Report             │
│  Price Alerts | Drawdown Alerts | Volume Spike Alerts       │
│  PostgreSQL Journal      | Wiki Feedback Stats            │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA & BACKTEST                            │
│  Market Data (CCXT/CoinGecko) → Feature Engineering        │
│  Event-Driven Backtest | Walk-Forward | Monte Carlo         │
│  Model Drift Detection                                      │
└─────────────────────────────────────────────────────────────┘
```

## Luồng Dữ liệu

```
Market Data → Feature Engineering → Strategy Signals
                                           │
                     Knowledge Engine ←────┘
                           │
                     Risk Manager (Regime-aware sizing + stops)
                           │
                     Order Manager → Exchange API
                           │
                     Journal + Telegram + Health API
                           │
                     Frontend Dashboard (Socket.IO real-time)
```

## Thành phần Chi tiết

### 1. Data Layer (`data/`)
- **`feed.py`**: Unified data fetcher, hỗ trợ CCXT và cache
- **`free_apis.py`**: CoinGecko API (free, no key required)
- **`external_apis.py`**: Các nguồn dữ liệu bổ sung
- **raw/**: Dữ liệu thô từ sàn (OHLCV, order book, funding rate)
- **processed/**: Dữ liệu đã clean, resample, fill missing

### 2. Strategy Layer (`strategies/`)
- **`base.py`**: Base class `BaseStrategy` với `Signal` và `StrategyContext`
- **`rule_based/`**: 3 chiến lược rule-based
  - `ema_trend.py`: EMA crossover + ATR stop
  - `monthly_breakout.py`: Monthly breakout với ATR filter
  - `grid_mean_reversion.py`: Grid trading cho ranging market
- **`ml_based.py`**: `MLStrategy` — adapter cho trained ML models với SL/TP management
- **`ensemble/regime_ensemble.py`**: **Chiến lược chính** — Regime detection + sub-strategy voting + Wiki validation
- **`regime_detector.py`**: Phát hiện trending/ranging/neutral dựa trên ATR và directional bias

### 3. Risk Layer (`risk/`)
- **`manager.py`**: `RiskManager` và `RegimeAwareRiskManager`
  - `PositionSizer`: fixed_fractional, atr_based, turtle_n, kelly
  - `StopLossManager`: fixed, ATR-based
  - `DrawdownGuard`: Circuit breaker với regime-specific limits
  - `TrailingStopManager`: Trailing stops trong backtest
  - `RegimeAwarePositionSizer`: Điều chỉnh risk theo regime (bull=1.0, bear=0.0, sideways=0.3)
  - `RegimeAwareStopLossManager`: ATR multipliers theo regime
- **`psychology.py`**: `PsychologicalEnforcer` — auto-pause sau consecutive losses, daily trade limit, revenge emotion detection, win-streak cooldown
- **`correlation_guard.py`**: Ngăn mở position quá correlated (>80%)
- **`portfolio_optimizer.py`**: Portfolio allocation
- **`monte_carlo.py`**: Monte Carlo simulation cho robustness

### 4. Execution Layer (`execution/`)
- **`live_trading.py`**: `LiveTradingEngine` — production engine đầy đủ
  - Graduation Gate: paper → live với criteria (30 days, max DD < 10%, Sharpe > 0.5, winrate > 40%, PF > 1.2)
  - Thread-safe: `threading.Lock()` bảo vệ shared state
  - Multi-symbol support với bar-time deduplication
  - Trailing stop + partial exit integration
  - Wiki feedback logging + auto min_alignment adjustment
- **`paper_trading.py`**: `PaperTradingEngine` — simulate fills với real-time price
- **`order_manager.py`**: `OrderManager` — validation, retry (exponential backoff), partial-fill tracking, persistence (JSONL)
- **`connectors/ccxt_connector.py`**: Kết nối Binance/Bybit qua CCXT
- **`trailing_stop.py`**: `TrailingStopManager` — activation_pct, trail_pct, min_profit_lock
- **`partial_exit.py`**: `PartialExitManager` — scale-out positions
- **`order_retry.py`**: `OrderRetryManager` — configurable retry với backoff
- **`slippage_tracker.py`**: Theo dõi slippage expected vs filled

### 5. ML Layer (`ml/`)
- **`pipelines/xgboost_pipeline.py`**: `MLClassifierPipeline` — train/predict với walk-forward
- **`pipelines/train.py`**: Training CLI
- **`pipelines/tuning.py`**: Hyperparameter tuning
- **`pipelines/threshold_optimizer.py`**: Tối ưu prediction threshold
- **`pipelines/rolling_retrain.py`**: Auto-retrain theo schedule
- **`features/engineering.py`**: 63+ features (price, volume, on-chain proxy, sentiment proxy, macro proxy)
- **`features/advanced.py`**: On-chain, sentiment, macro features (synthetic placeholders)
- **`features/selection.py`**: Feature selection, multicollinearity removal
- **`drift_detection.py`**: `ModelDriftMonitor` — PSI + error rate monitoring

### 6. Knowledge Engine (`knowledge_engine/`)
- **`rag.py`**: `WikiRAG` — retriever từ 683 wiki concepts
- **`signal_validator.py`**: `WikiSignalValidator` — validate signals against wiki principles
- **`embedder.py`**: Embedding model (sentence-transformers)
- **`vector_store.py`**: ChromaDB vector store
- **`ui.py`**: Streamlit chat UI

### 7. Backtest (`backtest/`)
- **`engine.py`**: `BacktestEngine` — event-driven, hỗ trợ stop-loss, trailing stops, commission, slippage
- **`enhanced_engine.py`**: Extended engine với regime tracking
- **`walkforward.py`**: `WalkForwardEngine` — walk-forward OOS validation
- **`run.py`**: Backtest runner CLI
- **`compare.py`**: So sánh nhiều chiến lược
- **`benchmark.py`**: Buy-and-hold benchmark

### 8. Monitoring (`monitoring/`)
- **`telegram.py`**: `TelegramAlerter` — bilingual EN/VN alerts
- **`health_server.py`**: `HealthServer` — HTTP health check server (port 8080)
- **`daily_report.py`**: `DailyReportGenerator` — daily P&L summary
- **`price_alerts.py`**: `PriceAlertManager` — price level alerts
- **`drawdown_alerts.py`**: `DrawdownAlertManager` — warning before circuit breaker
- **`volume_alerts.py`**: `VolumeAlertManager` — volume spike detection
- **`comparison_engine.py`**: So sánh performance

### 9. Journal (`journal/`)
- **`trade_logger.py`**: `TradeLogger` — PostgreSQL backend
  - Tables: trades, journal, snapshots, equity_snapshots, wiki_feedback
  - Methods: log_trade, log_journal, snapshot, trade_summary, emotion_distribution
  - Export: CSV, JSON

### 10. Backend API (`backend/api/`)
- **`main.py`**: FastAPI gateway với lifespan management
  - Endpoints: `/health`, `/api/v1/strategies`, `/api/v1/state`, `/api/v1/rebalance`, `/api/v1/market/ohlcv`, `/api/v1/market/tickers`
  - Socket.IO mounted at `/socket.io`
  - CORS cho Next.js dev server
- **`models.py`**: Pydantic models (StrategyState, Position, Alert, DailyReport, ...)
- **`aggregator.py`**: `StateAggregator` — poll và aggregate state từ multiple strategies
- **`socket_manager.py`**: `SocketManager` — broadcast real-time updates
- **`market_data.py`**: `MarketDataProvider` — OHLCV + tickers qua CoinGecko

### 11. Frontend (`frontend/`)
- Next.js 16 + TypeScript
- Dashboard pages: strategies, positions, backtest, wiki chat
- Kết nối backend qua REST API và Socket.IO

### 12. Config (`config/`)
- **`system.yaml`**: Config mẫu với đầy đủ defaults
- **`local.yaml`**: Config local (gitignored, copy từ system.yaml)

## Nguyên tắc Thiết kế

1. **Modularity**: Mỗi layer độc lập, giao tiếp qua interface rõ ràng
2. **Testability**: 71 unit tests, pytest-asyncio cho async tests
3. **Observability**: Log mọi quyết định, metric real-time (health server, Telegram)
4. **Config-driven**: Behavior thay đổi qua YAML config, không đụng code
5. **Fail-safe**: Drawdown guard, order retry, circuit breaker, auto-pause
6. **No overfitting**: Walk-forward validation bắt buộc, Monte Carlo
7. **Thread-safety**: `threading.Lock()` cho shared mutable state
8. **PostgreSQL journal**: All trading data persisted to PostgreSQL

## Tech Stack

| Layer | Tech |
|-------|------|
| Language | Python 3.11+ |
| Data | pandas, polars, CCXT, yfinance |
| Features | pandas-ta, custom engineering |
| ML | scikit-learn, XGBoost, PyTorch |
| Vector DB | ChromaDB |
| LLM | OpenAI API / Local |
| Execution | CCXT, websockets |
| Backtest | Custom event-driven |
| Config | Pydantic + YAML |
| DB | PostgreSQL |
| API | FastAPI, Socket.IO, uvicorn |
| Frontend | Next.js 16, TypeScript |
| Monitoring | Prometheus + Grafana, Telegram, Health HTTP server |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions → GHCR |
| Testing | pytest, pytest-asyncio |
| Linting | ruff |

## Các files Quan trọng

| File | Mục đích |
|------|----------|
| `config/local.yaml` | Config local (API keys, symbols, risk params) |
| `strategies/ensemble/regime_ensemble.py` | Chiến lược chính (production) |
| `risk/manager.py` | Risk management core |
| `execution/live_trading.py` | Production trading engine |
| `backtest/engine.py` | Event-driven backtest |
| `journal/trade_logger.py` | Trade journal (PostgreSQL) |
| `backend/api/main.py` | FastAPI gateway |
| `tests/` | Unit + integration tests |
