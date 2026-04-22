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
