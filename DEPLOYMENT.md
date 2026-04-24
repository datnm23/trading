# Hybrid Trading System — Deployment Guide

Hướng dẫn triển khai và khởi chạy hệ thống giao dịch trên máy mới.

## Yêu cầu hệ thống

- **OS**: Linux (Ubuntu 22.04+ khuyến nghị) hoặc macOS
- **Python**: 3.11+
- **Node.js**: 20+ (cho frontend)
- **Docker & Docker Compose**: v2+ (cho stack containerized)
- **RAM**: 4GB+ (8GB khuyến nghị cho ML + ChromaDB)
- **Disk**: 10GB+ (data + models)

## 1. Cài đặt dependencies

### Python

```bash
# Tạo virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Hoặc cài từ pyproject.toml (bao gồm dev dependencies)
pip install -e ".[dev]"
```

### Frontend (Next.js)

```bash
cd frontend
npm install
```

## 2. Cấu hình

### Environment variables

Tạo file `.env` ở root:

```env
# PostgreSQL
TRADING_DB_URL=postgresql://trader:trading123@localhost:5432/trading_journal

# Telegram Alerts (tùy chọn)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Exchange API (khi chạy live)
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
```

### Config files

- `config/system.yaml`: Cấu hình chính (symbols, timeframe, risk params)
- `config/local.yaml`: Override local (không commit)

## 3. Khởi động database

### Option A: Docker Compose (khuyến nghị)

```bash
# Khởi động toàn bộ stack
docker compose up -d

# Kiểm tra status
docker compose ps

# Logs
docker compose logs -f trading-bot
docker compose logs -f backend-api
```

### Option B: PostgreSQL local

```bash
# Ubuntu
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Tạo database
sudo -u postgres psql -c "CREATE USER trader WITH PASSWORD 'trading123';"
sudo -u postgres psql -c "CREATE DATABASE trading_journal OWNER trader;"
```

## 4. Khởi động services

### Bot (Paper Trading)

```bash
# Docker
docker compose up -d trading-bot

# Hoặc local (không khuyến nghị — cần setup environment phức tạp)
python -m execution.live_trading --config config/system.yaml --mode paper
```

### Backend API

```bash
# Docker
docker compose up -d backend-api

# Hoặc local
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --reload
```

### Frontend

```bash
cd frontend
npm run dev -- -p 3001
```

### Monitoring (Prometheus + Grafana)

```bash
docker compose up -d prometheus grafana
```

Truy cập Grafana: http://localhost:3000 (admin/admin)

## 5. Kiểm tra hoạt động

```bash
# Bot health
curl http://localhost:8080/health

# Backend API
curl http://localhost:8090/health
curl http://localhost:8090/api/v1/state
curl http://localhost:8090/api/v1/trades?limit=5

# Frontend
open http://localhost:3001

# Prometheus
open http://localhost:9090
```

## 6. Data

File OHLCV 1h đã có sẵn trong `data/raw/`:
- `BTC_USDT_1h.csv`
- `ETH_USDT_1h.csv`
- `SOL_USDT_1h.csv`

Bot sẽ tự động tải data mới khi chạy.

## 7. Chuyển sang Live Trading

**⚠️ Cảnh báo**: Live trading yêu cầu graduation gate:
- Paper trading 30 ngày có lãi
- Max drawdown < 10%
- Sharpe > 0.5
- Winrate > 40%

```bash
python -m execution.live_trading --config config/system.yaml --mode live
```

## Troubleshooting

| Lỗi | Nguyên nhân | Fix |
|-----|------------|-----|
| `ModuleNotFoundError` | Thiếu dependency | `pip install -r requirements.txt` |
| `Connection refused` | PostgreSQL chưa chạy | `docker compose up -d postgres` |
| `All connection attempts failed` | Bot chưa khởi động | `docker compose up -d trading-bot` |
| `EADDRINUSE:3001` | Port bị chiếm | `lsof -ti:3001 \| xargs kill -9` |
| CORS error | Frontend port sai | Kiểm tra `allow_origins` trong `backend/api/main.py` |

## File quan trọng

| File | Mục đích |
|------|---------|
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Stack containerized |
| `config/system.yaml` | Cấu hình bot |
| `.env` | Secrets (không commit) |
| `data/raw/*_1h.csv` | OHLCV data |
