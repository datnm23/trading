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

# Frontend API URL (cho production build)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

| Variable | Required | Mô tả |
|----------|----------|-------|
| `TRADING_DB_URL` | ✅ | PostgreSQL connection string |
| `NEXT_PUBLIC_API_URL` | ❌ | API base URL cho frontend build. Default: `http://localhost:8090` |
| `BINANCE_API_KEY` | ❌ (paper) / ✅ (live) | Binance API key |
| `BINANCE_SECRET` | ❌ (paper) / ✅ (live) | Binance API secret |
| `TELEGRAM_BOT_TOKEN` | ❌ | Telegram bot token cho alerts |
| `TELEGRAM_CHAT_ID` | ❌ | Telegram chat ID nhận alerts |
| `OPENAI_API_KEY` | ❌ | OpenAI key cho LLM-enhanced wiki validation |

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

#### Development

```bash
cd frontend
npm run dev -- -p 3001
```

#### Production Build (Static Export)

```bash
cd frontend
# Build static files (output: frontend/dist/)
npm run build

# Serve with any static file server, e.g.:
npx serve dist/ -p 3001
# Or copy dist/ to nginx, Vercel, Cloudflare Pages, S3, etc.
```

**Build output**: `frontend/dist/` contains pure static HTML/CSS/JS (~4MB).
- `index.html` — Dashboard
- `live.html`, `risk.html`, `reports.html`, `wiki.html`, `market.html` — Pages
- `wiki-index.json` — Static wiki data (required for /wiki)
- `_next/static/` — JS/CSS chunks

**Note**: `output: 'export'` is set in `next.config.ts`. This means:
- No server-side rendering (fine for a dashboard that calls a separate API)
- Socket.IO works client-side (connects to `API_BASE_URL`)
- Images are unoptimized (set in config)
- Not supported: Server Actions, cookies, dynamic routes without `generateStaticParams()`

### Monitoring (Prometheus + Grafana)

```bash
docker compose up -d prometheus grafana
```

Truy cập Grafana: http://localhost:3000 (admin/admin)

## 5. Deployment Options

### Option A: Docker Compose (All-in-One)

Phù hợp cho single VPS hoặc local development.

```bash
# Build frontend static files trước khi compose
cd frontend && npm run build && cd ..

# Khởi động toàn bộ stack
docker compose up -d
```

Frontend được serve qua nginx container từ `frontend/dist/`.

### Option B: Split Deploy (Backend VPS + Static Frontend)

Phù hợp cho production: backend trên VPS, frontend trên CDN.

**Backend** (VPS / EC2 / Droplet):
```bash
# Chỉ chạy backend services
docker compose up -d postgres trading-bot backend-api prometheus grafana
# Hoặc dùng systemd / PM2 cho backend-api
```

**Frontend** (Vercel / Cloudflare Pages / S3 + CloudFront):
```bash
cd frontend
# Build với API URL production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com npm run build

# Deploy dist/ lên static host
# Vercel: npx vercel --prod dist/
# Cloudflare Pages: npx wrangler pages deploy dist/
```

**Ưu điểm Split Deploy**:
- Frontend được phục vụ từ CDN toàn cầu (nhanh hơn)
- Backend API chỉ cần 1 instance (tiết kiệm)
- SSL + HTTPS tự động từ CDN
- Giảm tải cho VPS

**Lưu ý CORS**:
Nếu frontend và backend ở domain khác nhau, cập nhật `allow_origins` trong `backend/api/main.py`:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "https://your-frontend-domain.com",
]
```

## 6. Kiểm tra hoạt động

```bash
# Bot health
curl http://localhost:8080/health

# Backend API
curl http://localhost:8090/health
curl http://localhost:8090/api/v1/state
curl http://localhost:8090/api/v1/trades?limit=5
curl http://localhost:8090/api/v1/graduation

# Frontend
open http://localhost:3001

# Prometheus
open http://localhost:9090
```

## 7. Paper Trading Graduation

Truy cập `/graduation` trên frontend hoặc gọi API để xem tiến độ:

```bash
curl http://localhost:8090/api/v1/graduation | jq .
```

**Criteria** (cần đạt đủ 5 điều kiện):
| Gate | Threshold | Mô tả |
|------|-----------|-------|
| Days Traded | ≥ 30 | Số ngày có giao dịch |
| Return | > 0% | Lợi nhuận ròng |
| Max Drawdown | < 10% | Mức giảm tối đa từ đỉnh |
| Sharpe Ratio | > 0.5 | Risk-adjusted return |
| Winrate | > 40% | Tỷ lệ giao dịch thắng |

Khi đạt đủ điều kiện:
- Frontend hiển thị banner "Ready for Live Trading"
- Telegram alert tự động gửi tin nhắn thông báo
- Có thể chuyển sang live trading

## 7. Data

File OHLCV 1h đã có sẵn trong `data/raw/`:
- `BTC_USDT_1h.csv`
- `ETH_USDT_1h.csv`
- `SOL_USDT_1h.csv`

Bot sẽ tự động tải data mới khi chạy.

## 8. Chuyển sang Live Trading

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
