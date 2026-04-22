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
│                    KNOWLEDGE ENGINE                          │
│  (RAG + LLM + Wiki Anchor → Context-aware decisions)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   STRATEGY LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Rule-Based  │  │ ML Models   │  │ Ensemble / Selector │ │
│  │ (Trend,     │  │ (LSTM,      │  │ (Chọn chiến lược    │ │
│  │  Breakout)  │  │  XGBoost)   │  │  phù hợp context)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   RISK MANAGEMENT LAYER                      │
│  Position Sizing │ Stop Loss │ Max Drawdown │ Correlation   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER                            │
│  Paper Trading → Live Trading (Binance, Bybit, v.v.)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA & BACKTEST                            │
│  Market Data → Feature Engineering → Backtest Engine        │
└─────────────────────────────────────────────────────────────┘
```

## Thành phần Chi tiết

### 1. Data Layer (`data/`)
- **raw/**: Dữ liệu thô từ sàn (OHLCV, order book, funding rate)
- **processed/**: Dữ liệu đã clean, resample, fill missing
- **features/**: Feature engineering (technical indicators, on-chain metrics, macro signals)

### 2. Knowledge Layer (`knowledge/`)
- Dùng trực tiếp `crawl-wiki/` đã crawl (683 concepts)
- Embed vào vector DB (ChromaDB / Pinecone / Qdrant)
- Retrieval-Augmented Generation (RAG) để LLM có "tri thức" khi ra quyết định

### 3. Strategy Layer (`strategies/`)
- **rule_based/**: Chiến lược dựa trên quy tắc rõ ràng (trend following, breakout, mean reversion)
- **ml_based/**: Chiến lược dựa trên ML (dự đoán xu hướng, phân loại regime)
- **ensemble/**: Kết hợp nhiều chiến lược, chọn chiến lược phù hợp theo market regime

### 4. Risk Layer (`risk/`)
- Position sizing theo Kelly / Fixed Fractional / ATR-based
- Stop-loss: fixed, ATR-based, trailing, time-based
- Max drawdown circuit breaker
- Correlation check giữa các positions

### 5. Execution Layer (`execution/`)
- **connectors/**: Kết nối sàn (CCXT-based hoặc SDK riêng)
- **order_manager/**: Quản lý lệnh, retry logic, slippage tracking
- Paper trading trước live

### 6. ML Layer (`ml/`)
- **pipelines/**: Data preprocessing, feature selection, train/val/test split
- **models/**: LSTM, Transformer, XGBoost, v.v.
- **features/**: Custom feature engineering (not just TA-lib)

### 7. Knowledge Engine (`knowledge_engine/`)
- **rag/**: Retriever từ wiki concepts
- **llm/**: Prompt engineering, decision explanation
- Dùng để: giải thích tín hiệu, cảnh báo tâm lý, đánh giá regime

### 8. Backtest (`backtest/`)
- Event-driven backtest engine (không phải vectorized — chính xác hơn)
- Hỗ trợ: slippage, commission, market impact
- Walk-forward analysis, Monte Carlo simulation
- Out-of-sample validation

## Luồng Dữ liệu

```
Market Data → Feature Engineering → Strategy Signals
                                          │
                    Knowledge Engine ←────┘
                          │
                    Risk Manager
                          │
                    Order Manager → Exchange API
                          │
                    Logging & Journaling
```

## Nguyên tắc Thiết kế

1. **Modularity**: Mỗi layer độc lập, giao tiếp qua interface rõ ràng
2. **Testability**: Mỗi strategy, mỗi risk rule phải unit-test được
3. **Observability**: Log mọi quyết định, metric real-time (Grafana/Prometheus style)
4. **Config-driven**: Behavior thay đổi qua file config, không đụng code
5. **Fail-safe**: Mọi lỗi phải dừng an toàn, không tự động "gỡ gạc"
6. **No overfitting**: Backtest phải có OOS, walk-forward, Monte Carlo

## Tech Stack Đề xuất

| Layer | Tech |
|-------|------|
| Language | Python 3.11+ |
| Data | pandas, polars, yfinance, CCXT |
| Features | pandas-ta, talib, custom |
| ML | scikit-learn, XGBoost, PyTorch / TensorFlow |
| Vector DB | ChromaDB (local) hoặc Qdrant |
| LLM | OpenAI API / Claude / Local (Ollama) |
| Execution | CCXT, websockets |
| Backtest | Custom event-driven hoặc Backtrader/Zipline (reference) |
| Config | Pydantic + YAML |
| DB | PostgreSQL / SQLite cho journal, InfluxDB cho tick data |
| Monitoring | Prometheus + Grafana hoặc đơn giản hóa với loguru + streamlit |

## Phase Triển khai

| Phase | Mục tiêu | Thờigian ước tính |
|-------|----------|------------------|
| **P0: Foundation** | Cấu trúc dự án, data pipeline, backtest engine cơ bản | 1-2 tuần |
| **P1: Rule-Based** | 2-3 chiến lược rule-based (trend following, breakout), risk layer | 1-2 tuần |
| **P2: Knowledge** | Embed wiki, RAG pipeline, LLM decision support | 1 tuần |
| **P3: ML** | Feature engineering, train baseline models, ensemble | 2-3 tuần |
| **P4: Execution** | Paper trading, sàn connector, order manager | 1 tuần |
| **P5: Live** | Live trading với capital nhỏ, monitoring, journaling | Liên tục |

## Anti-patterns (điều KHÔNG làm)

- Không optimize quá mức entry signal mà bỏ qua exit/risk
- Không dùng leverage cao khi chưa robust
- Không overfit vào backtest (phải có OOS + walk-forward)
- Không để bot chạy không giám sát khi chưa qua paper trading đủ lâu
- Không tin hoàn toàn vào ML mà không có rule-based fallback

## Các files Quan trọng cần tạo ngay

- `config/system.yaml` — config toàn hệ thống
- `strategies/base.py` — base class cho mọi strategy
- `risk/manager.py` — risk management core
- `backtest/engine.py` — event-driven backtest
- `knowledge_engine/rag.py` — retriever từ wiki
- `execution/connectors/ccxt_connector.py` — kết nối sàn
