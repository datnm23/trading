# Hybrid Trading System

Hệ thống giao dịch hybrid kết hợp **rule-based strategies**, **machine learning**, và **knowledge anchor** từ Turtle Trading Wiki.

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Run tests
pytest tests/ -v

# 3. Run backtest với rule-based strategy
python -m backtest.run --strategy EMA-Trend --config config/local.yaml

# 4. Start backend API
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --reload

# 5. Start knowledge chat UI
streamlit run knowledge_engine/ui.py
```

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/project-overview-pdr.md`](docs/project-overview-pdr.md) | Product requirements, success criteria, risks |
| [`docs/architecture.md`](docs/architecture.md) | System architecture, component details, tech stack |
| [`docs/quickstart.md`](docs/quickstart.md) | Setup, tests, backtest, paper trading, API usage |
| [`docs/roadmap.md`](docs/roadmap.md) | Development phases, completion status |
| [`docs/deployment-guide.md`](docs/deployment-guide.md) | Docker, systemd, database migration |
| [`docs/code-standards.md`](docs/code-standards.md) | Coding conventions, testing, thread safety |
| [`docs/ml_xgboost_modification_plan.md`](docs/ml_xgboost_modification_plan.md) | ML experiment results (historical) |

## Thư mục

```
.
├── backend/api/         # FastAPI gateway + Socket.IO
├── backtest/            # Event-driven backtest engine
├── config/              # YAML configs (system.yaml + local.yaml)
├── crawl-wiki/          # Wiki crawler (683 concepts)
├── data/                # Market data pipeline
├── docs/                # Documentation
├── execution/           # Trading engines + connectors
├── frontend/            # Next.js 16 dashboard
├── journal/             # Trade journal (SQLite/PostgreSQL)
├── knowledge_engine/    # RAG + LLM + Signal validator
├── ml/                  # ML pipelines + feature engineering
├── monitoring/          # Alerts + health server
├── risk/                # Risk management
├── scripts/             # Utility scripts
├── strategies/          # Rule-based + ML strategies
└── tests/               # Unit + integration tests (71 tests)
```

## Key Features

- **RegimeEnsemble Strategy**: Kết hợp EMA-Trend + Monthly Breakout + Grid Mean Reversion, chọn theo market regime, validate qua 683 wiki concepts
- **Psychology Enforcement**: Tự động pause sau 3 consecutive losses, daily trade limit (10), revenge emotion detection, win-streak cooldown
- **Regime-Aware Risk**: Position sizing và stop-loss điều chỉnh theo bull/bear/sideways
- **Graduation Gate**: Chỉ cho phép live trading sau khi paper đạt criteria (30 days, DD < 10%, Sharpe > 0.5)
- **Full Safety Stack**: Trailing stops, partial exits, correlation guard, order retry, slippage tracking
- **Real-time Monitoring**: Prometheus + Grafana, Telegram alerts (bilingual EN/VN), health HTTP server, daily reports
- **Backend API**: FastAPI + Socket.IO cho Next.js frontend
- **PostgreSQL Journal**: Trade journal + wiki feedback trên PostgreSQL
- **Containerized**: Docker Compose stack (PostgreSQL, Bot, API, Prometheus, Grafana, Node Exporter)
- **CI/CD**: GitHub Actions build Docker image → GitHub Container Registry

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific modules
pytest tests/test_risk.py -v
pytest tests/test_execution.py -v
pytest tests/test_backend_api.py -v
pytest tests/test_ml_integration.py -v
```

**Current coverage**: 71 tests passing (risk, execution, journal, psychology, drift, knowledge, backend API, ML integration).

## Triết lý

> "Hệ thống giao dịch không chỉ là tìm một ý tưởng đúng, mà là vận hành đúng ý tưởng đó trong nhiều điều kiện thị trường khác nhau."

— *Turtle Trading Wiki*

## Production Deployment & Data Migration

### Chạy Paper Trading 24/7

```bash
# 1. Khởi động bot (systemd auto-restart)
systemctl --user start paper-trade.service

# 2. Xem log
journalctl --user -u paper-trade.service -f

# 3. Health check
curl http://localhost:8080/health

# 4. Dashboard
streamlit run scripts/dashboard.py --server.port 8501
```

### Chuyển máy / Migration Database

Bot dùng PostgreSQL (Docker). Data không tự động đi theo khi chuyển máy.

#### Export (máy cũ)
```bash
docker exec trading-postgres pg_dump -U trader trading_journal > trading_backup.sql
```

#### Import (máy mới)
```bash
# 1. Khởi động PostgreSQL container
docker run -d \
  --name trading-postgres \
  -e POSTGRES_USER=trader \
  -e POSTGRES_PASSWORD=trading123 \
  -e POSTGRES_DB=trading_journal \
  -p 5432:5432 \
  -v ./data/postgres:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine

# 2. Import data
cat trading_backup.sql | docker exec -i trading-postgres psql -U trader -d trading_journal

# 3. Kiểm tra
docker exec trading-postgres psql -U trader -d trading_journal -c "SELECT COUNT(*) FROM trades;"
```

#### Hoặc dùng Cloud PostgreSQL (Khuyến nghị)

Sửa `config/system.yaml`:
```yaml
journal:
  db_url: "postgresql://user:password@your-db-host:5432/trading_journal"
```

Các dịch vụ free tier phù hợp:
- **Supabase**: 500MB free
- **Neon**: 500MB free
- **AWS RDS**: $5-10/tháng

### Các service chạy nền

| Service | Port | Mô tả |
|---------|------|-------|
| Trading Bot | — | systemd `paper-trade.service` |
| Health API | 8080 | `curl localhost:8080/health` |
| Backend API | 8090 | FastAPI + Socket.IO gateway |
| Dashboard | 8501 | Streamlit real-time monitoring |
| PostgreSQL | 5432 | Journal + wiki feedback |

### Telegram Alerts

Set env vars trong `.env`:
```
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=-xxx
```

Bot gửi alert cho:
- 🟢/🔴 Trade signals
- 🔔 Price alerts (real-time)
- 🚨 Volume spikes
- ⚠️ Drawdown warnings
- 🧠 Psychology pauses
- ⚪ No-trade reasons (wiki detail)

## License

MIT — Dùng cho mục đích cá nhân / nội bộ.
