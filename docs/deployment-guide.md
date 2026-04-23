# Deployment Guide

## Overview

Hướng dẫn triển khai Hybrid Trading System từ môi trường development lên production.

## Môi trường Development

### Prerequisites
- Python 3.11+
- Docker + Docker Compose (khuyến nghị)
- Hoặc PostgreSQL local nếu chạy không qua Docker

### Option A: Docker Compose (Khuyến nghị)

Chạy toàn bộ stack bằng Docker Compose — bao gồm PostgreSQL, Trading Bot, Backend API, Prometheus, Grafana, và Export Cron.

```bash
# 1. Clone repo
git clone <repo-url>
cd hybrid-trading-system

# 2. Config env
cp .env.example .env
# Edit .env nếu cần (API keys, Telegram tokens)

# 3. Start stack
docker compose up -d

# 4. Verify services
 docker compose ps
# Expected: postgres, trading-bot, backend-api, prometheus, grafana, node-exporter running

# 5. Access services
# Grafana:    http://localhost:3000  (admin / changeme)
# Prometheus: http://localhost:9090
# API Health: http://localhost:8090/health
# Bot Health: http://localhost:8080/health
```

#### Services trong Docker Compose

| Service | Port | Mô tả |
|---------|------|-------|
| postgres | 5432 | Trading journal DB |
| trading-bot | 8080 | Main trading engine |
| backend-api | 8090 | FastAPI gateway |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Dashboard visualization |
| node-exporter | 9100 | Host OS metrics |
| export-journal | — | Cron export (10:00 UTC) |

#### Export cron (10:00 UTC)

```bash
# Chạy export container
docker compose --profile export up -d export-journal

# Hoặc chạy thủ công
docker compose exec trading-bot python scripts/export_journal.py --output-dir ./data/exports
```

#### View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f trading-bot
docker compose logs -f backend-api
```

#### Stop stack

```bash
docker compose down
# Hoặc xóa cả volumes
docker compose down -v
```

### Option B: Local Python (không Docker)

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start PostgreSQL (nếu chưa có)
docker run -d --name trading-postgres \
  -e POSTGRES_USER=trader \
  -e POSTGRES_PASSWORD=trading123 \
  -e POSTGRES_DB=trading_journal \
  -p 5432:5432 \
  postgres:16-alpine

# 4. Copy config
cp config/system.yaml config/local.yaml
# Edit config/local.yaml với API keys, symbols, risk params
```

### Config quan trọng trong `config/local.yaml`

```yaml
# System mode: paper | live
system:
  mode: "paper"

# Execution
execution:
  paper: true
  exchange_id: "binance"
  api_key: ""           # Set via env var EXCHANGE_API_KEY
  api_secret: ""        # Set via env var EXCHANGE_API_SECRET
  testnet: true

# Journal — PostgreSQL only
journal:
  db_url: "postgresql://trader:trading123@localhost:5432/trading_journal"

# Monitoring
monitoring:
  alert_telegram: true
  telegram_bot_token: ""    # Set via env var TELEGRAM_BOT_TOKEN
  telegram_chat_id: ""      # Set via env var TELEGRAM_CHAT_ID
  health_port: 8080
```

## Chạy Paper Trading 24/7

### systemd Service (Linux)

Tạo file `~/.config/systemd/user/paper-trade.service`:

```ini
[Unit]
Description=Hybrid Trading Paper Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/<user>/hybrid-trading-system
Environment="PATH=/home/<user>/hybrid-trading-system/.venv/bin"
Environment="PYTHONPATH=/home/<user>/hybrid-trading-system"
Environment="TELEGRAM_BOT_TOKEN=<token>"
Environment="TELEGRAM_CHAT_ID=<chat-id>"
Environment="EXCHANGE_API_KEY=<key>"
Environment="EXCHANGE_API_SECRET=<secret>"
ExecStart=/home/<user>/hybrid-trading-system/.venv/bin/python -m execution.live_trading --config config/local.yaml --mode paper
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
# Enable và start
systemctl --user daemon-reload
systemctl --user enable paper-trade.service
systemctl --user start paper-trade.service

# Xem log
journalctl --user -u paper-trade.service -f

# Stop
systemctl --user stop paper-trade.service
```

### Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080 8090

CMD ["python", "-m", "execution.live_trading", "--config", "config/local.yaml", "--mode", "paper"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  trading-bot:
    build: .
    container_name: trading-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - EXCHANGE_API_KEY=${EXCHANGE_API_KEY}
      - EXCHANGE_API_SECRET=${EXCHANGE_API_SECRET}
    volumes:
      - ./data:/app/data
      - ./config/local.yaml:/app/config/local.yaml:ro
    ports:
      - "8080:8080"
      - "8090:8090"
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    container_name: trading-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=trader
      - POSTGRES_PASSWORD=trading123
      - POSTGRES_DB=trading_journal
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  grafana:
    image: grafana/grafana:latest
    container_name: trading-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning
    depends_on:
      - trading-bot
```

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop
docker-compose down
```

## Backend API Deployment

### Standalone API Server

```bash
# Production mode (no reload)
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --workers 4

# Behind nginx reverse proxy
```

### nginx Config

```nginx
server {
    listen 80;
    server_name trading-api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8090;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io/ {
        proxy_pass http://localhost:8090;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## CI/CD — GitHub Actions

### Pipeline

File: `.github/workflows/ci.yml`

| Stage | Trigger | Job |
|-------|---------|-----|
| Test | Push/PR to main/develop | pytest + ruff lint |
| Build | Push to main (after test pass) | Build + push Docker image to GHCR |

### Image Registry

- **Registry**: `ghcr.io/<owner>/hybrid-trading-system`
- **Tags**: `latest`, `<git-sha>`
- **Permissions**: Repo cần `packages: write` trong workflow

### Local pull từ GHCR

```bash
# Login (dùng GitHub PAT)
echo $GITHUB_PAT | docker login ghcr.io -u <USERNAME> --password-stdin

# Pull latest
docker pull ghcr.io/<owner>/hybrid-trading-system:latest

# Update compose để dùng image thay vì build
docker compose pull
docker compose up -d
```

## Database Migration

### SQLite → PostgreSQL

```bash
# 1. Start PostgreSQL container
docker run -d \
  --name trading-postgres \
  -e POSTGRES_USER=trader \
  -e POSTGRES_PASSWORD=trading123 \
  -e POSTGRES_DB=trading_journal \
  -p 5432:5432 \
  -v ./data/postgres:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine

# 2. Update config/local.yaml
# journal:
#   db_url: "postgresql://trader:trading123@localhost:5432/trading_journal"

# 3. Migrate data
python -c "
from journal.trade_logger import TradeLogger
pg = TradeLogger(db_url='postgresql://trader:trading123@localhost:5432/trading_journal')
pg.migrate_from_sqlite('./data/journal.db')
"
```

### Backup PostgreSQL

```bash
# Export
docker exec trading-postgres pg_dump -U trader trading_journal > trading_backup.sql

# Import
cat trading_backup.sql | docker exec -i trading-postgres psql -U trader -d trading_journal

# Kiểm tra
docker exec trading-postgres psql -U trader -d trading_journal -c "SELECT COUNT(*) FROM trades;"
```

### Cloud PostgreSQL (Khuyến nghị cho production)

Sửa `.env` hoặc `config/local.yaml`:
```yaml
journal:
  db_url: "postgresql://user:password@your-db-host:5432/trading_journal"
```

Các dịch vụ free tier phù hợp:
- **Supabase**: 500MB free
- **Neon**: 500MB free
- **AWS RDS**: $5-10/tháng

## Cronjob — Xuất Data 10:00 UTC Hàng Ngày

Hệ thống tự động xuất toàn bộ journal data (trades, snapshots, wiki feedback) ra CSV và JSON mỗi ngày lúc 10:00 UTC.

### Cài đặt systemd Timer (Khuyến nghị)

```bash
# 1. Copy service và timer files
cp config/systemd/export-journal.service ~/.config/systemd/user/
cp config/systemd/export-journal.timer ~/.config/systemd/user/

# 2. Tạo log directory
mkdir -p ~/hybrid-trading-system/data/logs

# 3. Reload và enable
systemctl --user daemon-reload
systemctl --user enable export-journal.timer
systemctl --user start export-journal.timer

# 4. Kiểm tra status
systemctl --user list-timers --all
journalctl --user -u export-journal.service -n 20
```

### Output

- Export files: `./data/exports/<table>_<timestamp>.csv` và `.json`
- Log: `./data/logs/export_journal.log`

### Chạy thủ công

```bash
# Export all tables
python scripts/export_journal.py --output-dir ./data/exports --format both

# Export chỉ hôm nay
python scripts/export_journal.py --output-dir ./data/exports --today-only

# Export chỉ trades
python scripts/export_journal.py --tables trades --format csv
```

### crontab (Alternative)

```bash
# Mở crontab
crontab -e

# Thêm dòng sau (chạy 10:00 UTC = 17:00 ICT)
0 10 * * * cd /home/<user>/hybrid-trading-system && /home/<user>/hybrid-trading-system/.venv/bin/python scripts/export_journal.py --output-dir ./data/exports >> ./data/logs/export_journal.log 2>&1
```

## Live Trading Checklist

### Pre-live Requirements

- [ ] Paper trading profitable 30+ days
- [ ] Max drawdown < 10%
- [ ] Sharpe > 0.5
- [ ] Winrate > 40%
- [ ] Profit factor > 1.2
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Telegram alerts working
- [ ] Health server responding
- [ ] Database backed up
- [ ] Config reviewed (risk params, symbols, exposure limits)

### Graduation Gate

```bash
# Evaluate paper trading history
python -c "
from journal.trade_logger import TradeLogger
from execution.live_trading import GraduationGate

journal = TradeLogger(db_path='./data/journal.db')
result = GraduationGate.evaluate(journal)
print(f'Passed: {result[\"passed\"]}')
print(f'Reason: {result[\"reason\"]}')
"
```

### Switching to Live

```bash
# 1. Double-check config
# Ensure execution.paper = false
# Ensure testnet = false (if using real exchange)

# 2. Start in live mode
python -m execution.live_trading --config config/local.yaml --mode live

# 3. Monitor closely first 24h
# Watch Telegram alerts, health endpoint, journal logs
```

## Monitoring & Alerting

### Health Check

```bash
# Bot health
curl http://localhost:8080/health

# API health
curl http://localhost:8090/health

# Metrics
curl http://localhost:8080/metrics
```

### Telegram Alerts

Bot gửi alert cho:
- 🟢/🔴 Trade signals
- 🔔 Price alerts (real-time)
- 🚨 Volume spikes
- ⚠️ Drawdown warnings
- 🧠 Psychology pauses
- ⚪ No-trade reasons (wiki detail)
- 📊 Daily P&L summary (midnight UTC)

### Services

| Service | Port | Mô tả |
|---------|------|-------|
| Trading Bot | — | systemd / Docker |
| Health API | 8080 | `curl localhost:8080/health` |
| Backend API | 8090 | FastAPI + Socket.IO |
| Dashboard | 8501 | Streamlit |
| PostgreSQL | 5432 | Journal + wiki feedback |
| Grafana | 3000 | Metrics visualization |

## Troubleshooting

### Bot không khởi động

```bash
# Check logs
journalctl --user -u paper-trade.service -n 50

# Check config
python -c "import yaml; print(yaml.safe_load(open('config/local.yaml')))"

# Check dependencies
python -c "import ccxt; print(ccxt.__version__)"
```

### Database connection failed

```bash
# Test PostgreSQL connection
psql postgresql://trader:trading123@localhost:5432/trading_journal -c "SELECT 1"

# Check SQLite file
ls -la ./data/journal.db
```

### Telegram alerts not working

```bash
# Test Telegram
curl -s "https://api.telegram.org/bot<TOKEN>/getMe"

# Check env vars
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### Health server not responding

```bash
# Check port
netstat -tlnp | grep 8080

# Check firewall
sudo ufw status
```

## Security Best Practices

1. **Never commit API keys** — dùng env vars hoặc `.env` (gitignored)
2. **Use testnet first** — Binance testnet cho paper trading
3. **Limit exchange permissions** — chỉ cấp quyền "Spot Trading", không "Withdraw"
4. **IP whitelist** — giới hạn IP truy cập exchange API
5. **Regular backups** — backup journal DB hàng ngày
6. **Monitor logs** — review logs định kỳ để phát hiện anomaly
