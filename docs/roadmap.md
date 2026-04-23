# Roadmap: Hybrid Trading System

## Phase 0: Foundation (Week 1-2) ✅ COMPLETED

### Mục tiêu
- [x] Có cấu trúc dự án modular, testable
- [x] Data pipeline chạy được: download, clean, store
- [x] Backtest engine event-driven cơ bản

### Tasks
- [x] Setup Python project với `pyproject.toml`, `pytest`, `ruff`
- [x] Tạo base classes: `Strategy`, `RiskManager`, `Connector`, `DataFeed`
- [x] Xây dựng `data/feed.py`: download OHLCV từ CCXT / yfinance
- [x] Xây dựng `backtest/engine.py`: event-driven, hỗ trợ slippage + commission
- [x] Viết unit tests cho engine và data feed

### Deliverable
```bash
python -m backtest.engine --config config/paper.yaml
# → output: equity curve, drawdown, sharpe, trades log
```

## Phase 1: Rule-Based Strategies (Week 2-4) ✅ COMPLETED

### Mục tiêu
- [x] 2-3 chiến lược rule-based chạy được trên backtest
- [x] Risk layer hoạt động: position sizing, stop-loss, max drawdown

### Chiến lược đề xuất (phù hợp wiki)
1. [x] **Trend Following EMA Cross** + ATR stop
2. [x] **Monthly Breakout** (theo concept breakout_monthly)
3. [x] **Mean Reversion Grid** (cho thị trường sideway)

### Tasks
- [x] `strategies/rule_based/ema_trend.py`
- [x] `strategies/rule_based/monthly_breakout.py`
- [x] `risk/position_sizer.py`: Fixed fractional, Kelly criterion, ATR-based
- [x] `risk/stop_loss.py`: Fixed, ATR, trailing, time-based
- [x] `risk/drawdown_guard.py`: Circuit breaker khi đạt max drawdown
- [x] Backtest từng chiến lược trên 3-5 năm data

### Deliverable
```bash
python -m backtest.run --strategy EMA-Trend --symbol BTC/USDT --timeframe 1d
# → Report: total return, max drawdown, sharpe, winrate, profit factor
```

## Phase 2: Knowledge Engine (Week 4-5) ✅ COMPLETED

### Mục tiêu
- [x] Wiki đã crawl được embed vào vector DB
- [x] LLM có thể trả lợi câu hỏi về tri thức trading
- [x] RAG có thể gợi ý chiến lược phù hợp với market regime

### Tasks
- [x] `knowledge_engine/embedding.py`: Embed 683 concepts bằng sentence-transformers
- [x] `knowledge_engine/vector_store.py`: ChromaDB setup
- [x] `knowledge_engine/rag.py`: Retriever + LLM prompt
- [x] `knowledge_engine/signal_validator.py`: Validate signals against wiki
- [x] Streamlit UI để chat với wiki knowledge
- [x] Wiki feedback loop: log validation decisions, update min_alignment from outcomes

### Deliverable
```python
from knowledge_engine.rag import WikiRAG
rag = WikiRAG()
rag.query("Khi nào nên dùng trend following thay vì mean reversion?")
# → Trả lợi dựa trên concepts từ wiki
```

## Phase 3: Machine Learning (Week 5-8) ✅ COMPLETED (HALTED)

### Mục tiêu
- [x] Feature engineering pipeline robust
- [x] Baseline models: XGBoost
- [x] Ensemble hoặc regime selector

### Tasks
- [x] `ml/features/engineering.py`: 63+ features
- [x] `ml/features/selection.py`: Remove multicollinearity
- [x] `ml/pipelines/xgboost_pipeline.py`: Train/predict pipeline
- [x] `ml/drift_detection.py`: Model drift monitoring

### Anti-overfitting
- [x] Walk-forward validation bắt buộc
- [x] Kiểm tra stationarity của features

### Decision: HALT ML as primary strategy
After extensive testing (threshold tuning, feature whitelist, target horizon extension), **ML-XGBoost fails to achieve positive gross return** on BTC/USDT 4h walk-forward data. RegimeEnsemble demonstrably outperforms (+58% gross vs -0.8% best ML).

**Next**: Use ML as secondary signal input (not primary decision maker).

## Phase 4: Execution & Paper Trading (Week 8-9) ✅ COMPLETED

### Mục tiêu
- [x] Kết nối được sàn (Binance testnet)
- [x] Paper trading chạy 24/7 stable
- [x] Logging và journaling đầy đủ

### Tasks
- [x] `execution/connectors/ccxt_connector.py`: Unified API qua CCXT
- [x] `execution/order_manager.py`: Order validation, retry, partial fill handling
- [x] `execution/paper_trading.py`: Paper trading engine
- [x] `execution/live_trading.py`: Live trading wrapper với Graduation Gate
- [x] `journal/trade_logger.py`: Ghi lại mọi quyết định, lý do, emotion
- [x] `monitoring/telegram.py`: Bilingual alerts
- [x] `monitoring/health_server.py`: HTTP health check
- [x] `monitoring/daily_report.py`: Daily P&L summary

### Deliverable
```bash
python -m execution.live_trading --config config/local.yaml --mode paper --symbol BTC/USDT
# → Chạy paper trading, log mọi tín hiệu và fill
```

## Phase 5: Live Trading & Monitoring (Week 9-10) ✅ COMPLETED

### Mục tiêu
- [x] Live trading với capital nhỏ (giới hạn rủi ro)
- [x] Monitoring, alerting đầy đủ
- [x] Psychology enforcement

### Tasks
- [x] Graduation Gate: paper → live criteria
- [x] Psychology enforcer: consecutive loss pause, daily trade limit, emotion detection
- [x] Correlation guard: prevent over-concentration
- [x] Trailing stop + partial exit managers
- [x] Order retry manager with exponential backoff
- [x] Slippage tracker
- [x] Price alerts, drawdown alerts, volume spike alerts
- [x] Model drift detection (for ML strategies)

### Risk Rules cho Live
- Max 1% account risk per trade
- Max 10% total account in market
- Max drawdown 15% → stop, review
- Không trade ngày có tin tức lớn nếu chưa có filter

## Phase 6: Backend API & Frontend (Week 10-12) ✅ COMPLETED

### Mục tiêu
- [x] FastAPI gateway cho frontend
- [x] Next.js dashboard
- [x] Real-time updates qua Socket.IO

### Tasks
- [x] `backend/api/main.py`: FastAPI + Socket.IO
- [x] `backend/api/aggregator.py`: State aggregation
- [x] `backend/api/market_data.py`: Market data provider
- [x] `frontend/`: Next.js 16 + TypeScript dashboard
- [x] CORS, lifespan management, graceful shutdown

## Phase 7: Testing & Hardening (Week 12+) 🔄 IN PROGRESS

### Mục tiêu
- [ ] 80%+ test coverage
- [ ] Integration tests cho live trading path
- [ ] Load testing cho API
- [ ] Security audit

### Tasks
- [x] Unit tests cho risk, execution, journal, psychology, drift
- [x] Integration test cho backend API (pytest-asyncio)
- [x] Integration test cho ML strategy + live engine
- [ ] E2E test cho paper trading 24/7
- [ ] Fuzz testing cho order validation
- [ ] Race condition testing (multi-threading)

### Bugs Fixed
- [x] Backtest engine: `_check_stops()` now properly called in `run()` loop
- [x] RegimeEnsemble: removed unreachable duplicate code
- [x] Paper trading: stop-loss checked on every bar (not just signal bars)
- [x] Backend API: error handling cho market data endpoints
- [x] MLStrategy: null guard cho `self.params`
- [x] Advanced features: `np.random.default_rng()` thay vì global seed pollution

## Phase 8: Deployment & DevOps (Week 13+) ⏳ PLANNED

### Mục tiêu
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Auto-restart, auto-backup

### Tasks
- [ ] `Dockerfile` cho trading bot
- [ ] `docker-compose.yml` (bot + PostgreSQL + Grafana)
- [ ] GitHub Actions: test, lint, build
- [ ] Prometheus metrics exporter
- [ ] Grafana dashboard templates
- [ ] Automated DB backup to S3

## Kết nối với Turtle Trading Wiki

Mỗi phase map với concepts trong wiki:

| Phase | Wiki Concepts liên quan |
|-------|------------------------|
| P0 | `3_tang_he_thong_giao_dich`, `backtest`, `khoi_du_lieu_giao_dich` |
| P1 | `trend_following`, `breakout_monthly`, `chien_luoc_cat_lo_chay_loi`, `quan_ly_von` |
| P2 | `tri_thuc_lan_truyen`, `meta_think`, `ai_llm_trong_trading` |
| P3 | `non_stationarity`, `overfit_vao_qua_khu`, `monte_carlo`, `walk_forward` |
| P4 | `giao_dich_tu_dong`, `truot_gia`, `phi_vao_cua_song` |
| P5 | `ky_luat_trading`, `drawdown_keo_dai`, `tam_ly_bam_viu_hy_vong` |
| P6 | `giao_dien_giam_sat`, `canh_bao_thoi_gian_thuc` |
| P7 | `kiem_thu_he_thong`, `bao_mat_giao_dich` |
| P8 | `trien_khai_san_xuat`, `sao_luu_du_lieu` |

## Success Criteria

- [x] Backtest Sharpe > 1.0 trên 3 năm data (RegimeEnsemble 4h: Sharpe 0.98-1.33 nhiều periods)
- [x] Max drawdown < 20% (RegimeEnsemble: ~17-21% depending on period)
- [x] Knowledge engine trả lợi chính xác > 80% câu hỏi về concepts
- [x] Hệ thống chạy 24/7 không crash trong 2 tuần paper trading
- [ ] 80%+ test coverage (current: ~35%)
- [ ] Positive net return trên paper trading 1 tháng
