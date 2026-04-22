# Hybrid Trading System

Hệ thống giao dịch hybrid kết hợp **rule-based strategies**, **machine learning**, và **knowledge anchor** từ Turtle Trading Wiki.

## Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Copy and edit config
cp config/system.yaml config/local.yaml
# Edit API keys, symbols, risk params

# 3. Run backtest với rule-based strategy
python -m backtest.run --strategy EMA-Trend --config config/local.yaml

# 4. Start knowledge chat UI
streamlit run knowledge_engine/ui.py
```

## Kiến trúc

Xem chi tiết tại [`docs/architecture.md`](docs/architecture.md).

## Roadmap

Xem chi tiết tại [`docs/roadmap.md`](docs/roadmap.md).

## Thư mục

```
.
├── data/               # Market data pipeline
├── knowledge/          # Wiki anchor (crawl-wiki/)
├── strategies/         # Rule-based + ML strategies
├── backtest/           # Event-driven backtest engine
├── risk/               # Risk management layer
├── execution/          # Exchange connectors + order manager
├── ml/                 # ML models + feature engineering
├── knowledge_engine/   # RAG + LLM decision support
├── config/             # YAML configs
├── notebooks/          # Research notebooks
├── tests/              # Unit + integration tests
└── docs/               # Documentation
```

## Triết lý

> "Hệ thống giao dịch không chỉ là tìm một ý tưởng đúng, mà là vận hành đúng ý tưởng đó trong nhiều điều kiện thị trường khác nhau."

— *Turtle Trading Wiki*

## License

MIT — Dùng cho mục đích cá nhân / nội bộ.
