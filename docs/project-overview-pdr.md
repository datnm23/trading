# Project Overview — PDR

## Product Development Requirements

### Tên sản phẩm
**Hybrid Trading System** — Hệ thống giao dịch tự động kết hợp rule-based, machine learning, và knowledge anchor.

### Mục tiêu
Xây dựng hệ thống giao dịch tự động **robust, testable, và có lợi thế bền vững** dựa trên:
1. **Rule-based strategies** — Trend following, breakout, mean reversion
2. **Machine Learning** — XGBoost classifier cho dự đoán xu hướng
3. **Knowledge Anchor** — 683 concepts từ Turtle Trading Wiki làm "la bàn" định hướng

### Target Users
- Cá nhân tự động hóa chiến lược giao dịch crypto
- Prop traders cần backtest và risk management chặt chẽ
- Quant researchers muốn kết hợp ML với domain knowledge

### Key Differentiators
- **Wiki-anchored decisions**: Mọi tín hiệu được validate chống lại 683 concepts từ Turtle Trading Wiki
- **Psychology enforcement**: Tự động pause sau consecutive losses, giảm size khi revenge/FOMO
- **Regime-aware risk**: Position sizing và stop-loss điều chỉnh theo bull/bear/sideways
- **Graduation Gate**: Chỉ cho phép live trading sau khi paper trading đạt criteria
- **Bilingual alerts**: Telegram alerts song ngữ EN/VN

## System Requirements

### Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| F1 | Fetch OHLCV data từ Binance/CCXT | P0 | ✅ Done |
| F2 | Event-driven backtest với slippage + commission | P0 | ✅ Done |
| F3 | 3 rule-based strategies (EMA, Breakout, Grid) | P0 | ✅ Done |
| F4 | Regime detection (trending/ranging/neutral) | P0 | ✅ Done |
| F5 | RegimeEnsemble strategy (vote + wiki validation) | P0 | ✅ Done |
| F6 | ML XGBoost pipeline | P1 | ✅ Done (halted as primary) |
| F7 | Position sizing (Kelly, Fixed Fractional, ATR, Turtle N) | P0 | ✅ Done |
| F8 | Stop-loss (fixed, ATR, trailing) | P0 | ✅ Done |
| F9 | Drawdown circuit breaker | P0 | ✅ Done |
| F10 | Psychology enforcer | P1 | ✅ Done |
| F11 | Correlation guard | P1 | ✅ Done |
| F12 | Paper trading engine | P0 | ✅ Done |
| F13 | Live trading engine với Graduation Gate | P0 | ✅ Done |
| F14 | Order manager + retry logic | P0 | ✅ Done |
| F15 | Trade journal (PostgreSQL) | P0 | ✅ Done |
| F16 | Telegram alerts (bilingual) | P1 | ✅ Done |
| F17 | Health HTTP server | P1 | ✅ Done |
| F18 | Daily report generator | P1 | ✅ Done |
| F19 | Model drift detection | P2 | ✅ Done |
| F20 | Wiki feedback loop | P1 | ✅ Done |
| F21 | FastAPI backend + Socket.IO | P2 | ✅ Done |
| F22 | Next.js frontend dashboard | P2 | ✅ Done |
| F23 | Price/drawdown/volume alerts | P2 | ✅ Done |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NF1 | Uptime | 99.9% (auto-restart) |
| NF2 | Latency | < 5s từ signal đến order submission |
| NF3 | Throughput | 10+ symbols simultaneously |
| NF4 | Backtest accuracy | Slippage + commission modeled |
| NF5 | Test coverage | 80%+ (current: ~35%) |
| NF6 | Config-driven | Behavior change via YAML, no code change |
| NF7 | Fail-safe | Auto-halt on error, no self-healing without review |
| NF8 | Observability | Log every decision, real-time health checks |

## Architecture Summary

### High-Level Diagram

```
Frontend (Next.js) ←→ Backend API (FastAPI + Socket.IO)
                              │
                              ▼
                    Knowledge Engine (RAG + Wiki)
                              │
                              ▼
                    Strategy Layer (Rule + ML + Ensemble)
                              │
                              ▼
                    Risk Layer (Sizing + Stops + Psychology)
                              │
                              ▼
                    Execution (Paper → Live via CCXT)
                              │
                              ▼
                    Journal + Alerts + Health Monitor
```

### Data Flow

1. **Data Feed** fetches OHLCV từ Binance/CoinGecko
2. **Strategy Layer** generates signals (rule-based hoặc ML)
3. **Knowledge Engine** validates signals against wiki concepts
4. **Risk Layer** checks exposure, drawdown, correlation, psychology
5. **Execution Layer** submits orders qua CCXT (paper hoặc live)
6. **Journal** logs trades, emotions, wiki feedback
7. **Monitoring** sends alerts và exposes health metrics
8. **Backend API** aggregates state cho frontend

## Performance Metrics

### Walk-Forward Results (BTC/USDT 4h)

| Strategy | Net Return | Gross Return | Trades | Win Periods |
|----------|-----------|-------------|--------|-------------|
| RegimeEnsemble | **+53.7%** | +58.0% | 33 | 5/9 |
| BuyHold | +18.4% | +19.0% | 9 | 5/9 |
| ML-XGBoost | -4.0% | -0.8% | 55 | — |

### Key Insights
- RegimeEnsemble outperforms both BuyHold và ML-XGBoost
- ML không có alpha đủ mạnh để vượt transaction costs
- Wiki validation + psychology enforcement là yếu tố quyết định

## Tech Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.11+ |
| Data | pandas, polars, CCXT |
| ML | scikit-learn, XGBoost, PyTorch |
| Vector DB | ChromaDB |
| LLM | OpenAI API / Local |
| API | FastAPI, Socket.IO, uvicorn |
| Frontend | Next.js 16, TypeScript |
| DB | PostgreSQL |
| Monitoring | loguru, Telegram, Health HTTP |
| Testing | pytest, pytest-asyncio |
| Linting | ruff |

## Project Structure

```
hybrid-trading-system/
├── backend/api/           # FastAPI gateway
├── backtest/              # Event-driven backtest engine
├── config/                # YAML configs
├── crawl-wiki/            # Wiki crawler (683 concepts)
├── data/                  # Data pipeline
├── docs/                  # Documentation
├── execution/             # Trading engines + connectors
├── frontend/              # Next.js dashboard
├── journal/               # Trade journal (PostgreSQL)
├── knowledge_engine/      # RAG + LLM + Signal validator
├── ml/                    # ML pipelines + feature engineering
├── monitoring/            # Alerts + health server
├── risk/                  # Risk management
├── scripts/               # Utility scripts
├── strategies/            # Rule-based + ML strategies
└── tests/                 # Unit + integration tests
```

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Overfitting backtest | High | High | Walk-forward, Monte Carlo, OOS validation |
| Exchange API failure | Medium | High | Retry logic, circuit breaker, paper mode fallback |
| Drawdown vượt ngưỡng | Medium | Critical | Auto-halt, psychology pause, regime-aware sizing |
| ML model degradation | Medium | Medium | Drift detection, auto-retrain schedule |
| Data quality issues | Medium | High | Multiple data sources, validation, cache |
| Security breach (API keys) | Low | Critical | Env vars, IP whitelist, limited permissions |
| Overtrading | Medium | Medium | Daily trade limit, cooldown, psychology enforcer |

## Success Criteria

### Phase 1 (Completed)
- [x] Event-driven backtest engine
- [x] 3 rule-based strategies
- [x] Risk management layer
- [x] Paper trading engine

### Phase 2 (Completed)
- [x] Knowledge engine (RAG + wiki validation)
- [x] ML pipeline (XGBoost)
- [x] Live trading engine
- [x] Telegram alerts

### Phase 3 (Completed)
- [x] Backend API (FastAPI + Socket.IO)
- [x] Frontend dashboard (Next.js)
- [x] Monitoring stack (health, alerts, daily reports)

### Phase 4 (In Progress)
- [ ] 80%+ test coverage
- [ ] E2E testing for live trading path
- [ ] Docker deployment
- [ ] CI/CD pipeline

### Phase 5 (Planned)
- [ ] Positive net return trên paper trading 1 tháng
- [ ] Live trading với capital nhỏ
- [ ] Performance monitoring (Prometheus + Grafana)

## Glossary

| Term | Definition |
|------|------------|
| Regime | Trạng thái thị trường: trending, ranging, neutral |
| Ensemble | Kết hợp nhiều chiến lược, chọn theo regime |
| Walk-forward | Validation method: train trên quá khứ, test trên tương lai |
| OOS | Out-of-sample: data không nhìn thấy trong training |
| RAG | Retrieval-Augmented Generation: LLM + vector search |
| Graduation Gate | Criteria để chuyển từ paper → live |
| PSI | Population Stability Index: đo lường drift |
| ATR | Average True Range: đo volatility |
| SL/TP | Stop-loss / Take-profit |
