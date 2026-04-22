# Roadmap: Hybrid Trading System

## Phase 0: Foundation (Week 1-2)

### Mục tiêu
- Có cấu trúc dự án modular, testable
- Data pipeline chạy được: download, clean, store
- Backtest engine event-driven cơ bản

### Tasks
- [ ] Setup Python project với `pyproject.toml`, `pytest`, `ruff`
- [ ] Tạo base classes: `Strategy`, `RiskManager`, `Connector`, `DataFeed`
- [ ] Xây dựng `data/feed.py`: download OHLCV từ CCXT / yfinance
- [ ] Xây dựng `backtest/engine.py`: event-driven, hỗ trợ slippage + commission
- [ ] Viết unit tests cho engine và data feed

### Deliverable
```bash
python -m backtest.engine --config config/paper.yaml
# → output: equity curve, drawdown, sharpe, trades log
```

## Phase 1: Rule-Based Strategies (Week 2-4)

### Mục tiêu
- 2-3 chiến lược rule-based chạy được trên backtest
- Risk layer hoạt động: position sizing, stop-loss, max drawdown

### Chiến lược đề xuất (phù hợp wiki)
1. **Trend Following EMA Cross** + ATR stop
2. **Monthly Breakout** (theo concept breakout_monthly)
3. **Mean Reversion Grid** (cho thị trường sideway)

### Tasks
- [ ] `strategies/rule_based/ema_trend.py`
- [ ] `strategies/rule_based/monthly_breakout.py`
- [ ] `risk/position_sizer.py`: Fixed fractional, Kelly criterion, ATR-based
- [ ] `risk/stop_loss.py`: Fixed, ATR, trailing, time-based
- [ ] `risk/drawdown_guard.py`: Circuit breaker khi đạt max drawdown
- [ ] Backtest từng chiến lược trên 3-5 năm data

### Deliverable
```bash
python -m backtest.run --strategy EMA-Trend --symbol BTC/USDT --timeframe 1d
# → Report: total return, max drawdown, sharpe, winrate, profit factor
```

## Phase 2: Knowledge Engine (Week 4-5)

### Mục tiêu
- Wiki đã crawl được embed vào vector DB
- LLM có thể trả lợi câu hỏi về tri thức trading
- RAG có thể gợi ý chiến lược phù hợp với market regime

### Tasks
- [ ] `knowledge_engine/embedding.py`: Embed 683 concepts bằng OpenAI / sentence-transformers
- [ ] `knowledge_engine/vector_store.py`: ChromaDB setup
- [ ] `knowledge_engine/rag.py`: Retriever + LLM prompt
- [ ] `knowledge_engine/regime_advisor.py`: Gợi ý chiến lược dựa trên tri thức
- [ ] Streamlit UI để chat với wiki knowledge

### Deliverable
```python
from knowledge_engine.rag import WikiRAG
rag = WikiRAG()
rag.query("Khi nào nên dùng trend following thay vì mean reversion?")
# → Trả lợi dựa trên concepts từ wiki
```

## Phase 3: Machine Learning (Week 5-8)

### Mục tiêu
- Feature engineering pipeline robust
- Baseline models: XGBoost, LSTM
- Ensemble hoặc regime selector

### Tasks
- [ ] `ml/features/engineering.py`: Tạo 50+ features (price, volume, on-chain, macro)
- [ ] `ml/features/selection.py`: Remove multicollinearity, feature importance
- [ ] `ml/pipelines/split.py**: Walk-forward split (không random shuffle!)
- [ ] `ml/models/xgboost_classifier.py`: Phân loại Up/Down/Neutral
- [ ] `ml/models/lstm_regressor.py`: Dự đoán return
- [ ] `ml/ensemble.py`: Kết hợp ML + rule-based signals
- [ ] Đánh giá: precision, recall, f1, và **profitability trên backtest**

### Anti-overfitting
- Walk-forward validation bắt buộc
- Kiểm tra stationarity của features
- Monte Carlo permutation test
- Không dùng future data (look-ahead bias check)

### Deliverable
```bash
python -m ml.train --model xgboost --symbol BTC/USDT --walk-forward
python -m ml.predict --model xgboost --date 2026-04-21
```

## Phase 4: Execution & Paper Trading (Week 8-9)

### Mục tiêu
- Kết nối được sàn (Binance / Bybit testnet)
- Paper trading chạy 24/7 stable
- Logging và journaling đầy đủ

### Tasks
- [ ] `execution/connectors/ccxt_connector.py`: Unified API qua CCXT
- [ ] `execution/order_manager.py`: Order validation, retry, partial fill handling
- [ ] `execution/paper_trading.py`: Paper trading engine giả lập fill
- [ ] `execution/live_trading.py`: Live trading wrapper
- [ ] `journal/trade_logger.py`: Ghi lại mọi quyết định, lý do, emotion
- [ ] `monitoring/dashboard.py`: Streamlit/Grafana xem equity, positions, P&L

### Deliverable
```bash
python -m execution.paper_trading --config config/paper_btc.yaml
# → Chạy paper trading 1 tuần, log mọi tín hiệu và fill
```

## Phase 5: Live Trading & Continuous Improvement (Week 9+)

### Mục tiêu
- Live trading với capital nhỏ (giới hạn rủi ro)
- Monitoring, alerting
- Continuous retraining / adaptation

### Tasks
- [ ] Deploy trên VPS / cloud (AWS/GCP)
- [ ] Alert: Telegram/Slack khi có tín hiệu, lỗi, drawdown vượt ngưỡng
- [ ] `ml/retrain.py`: Tự động retrain khi có đủ data mới
- [ ] `knowledge_engine/update.py**: Crawl wiki mới nhất định kỳ
- [ ] Monthly review: review trades, update strategy nếu cần

### Risk Rules cho Live
- Max 1% account risk per trade
- Max 10% total account in market
- Max drawdown 15% → stop, review
- Không trade ngày có tin tức lớn nếu chưa có filter

## Kết nối với Turtle Trading Wiki

Mỗi phase nên map với concepts trong wiki:

| Phase | Wiki Concepts liên quan |
|-------|------------------------|
| P0 | `3_tang_he_thong_giao_dich`, `backtest`, `khoi_du_lieu_giao_dich` |
| P1 | `trend_following`, `breakout_monthly`, `chien_luoc_cat_lo_chay_loi`, `quan_ly_von` |
| P2 | `tri_thuc_lan_truyen`, `meta_think`, `ai_llm_trong_trading` |
| P3 | `non_stationarity`, `overfit_vao_qua_khu`, `monte_carlo`, `walk_forward` |
| P4 | `giao_dich_tu_dong`, `truot_gia`, `phi_vao_cua_song` |
| P5 | `ky_luat_trading`, `drawdown_keo_dai`, `tam_ly_bam_viu_hy_vong` |

## Success Criteria

- [ ] Backtest Sharpe > 1.0 trên 3 năm data
- [ ] Max drawdown < 20%
- [ ] Paper trading 1 tháng: lợi nhuận > -5%, drawdown < 10%
- [ ] Knowledge engine trả lợi chính xác > 80% câu hỏi về concepts
- [ ] Hệ thống chạy 24/7 không crash trong 2 tuần paper trading
