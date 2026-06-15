# VN Stock Advisory Platform

Platform tư vấn chứng khoán Việt Nam cung cấp **screening**, **định giá**, và **khuyến nghị BUY/SELL/HOLD** dựa trên phân tích cơ bản và kỹ thuật. Advisory-only, không tự đặt lệnh.

## Quick Start

```bash
# 1. Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Run tests
pytest tests/ -v

# 3. Start backend API (FastAPI)
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --reload

# 4. Start frontend (Next.js, new terminal)
cd frontend
npm install
npm run dev

# 5. Access frontend at http://localhost:3000
```

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/system-architecture.md`](docs/system-architecture.md) | Architecture overview, module details, data flow |
| [`docs/codebase-summary.md`](docs/codebase-summary.md) | Directory structure, module responsibilities, statistics |
| [`docs/project-changelog.md`](docs/project-changelog.md) | MVP-1 pivot summary: what's new, removed, changed |
| [`docs/vn-stock-advisory-design.md`](docs/vn-stock-advisory-design.md) | Design decisions, roadmap, risks, next steps |
| [`docs/code-standards.md`](docs/code-standards.md) | Coding conventions, naming, testing standards |
| [`docs/deployment-guide.md`](docs/deployment-guide.md) | Docker, systemd, database migration |

## Cấu trúc Thư mục

```
.
├── backend/api/         # FastAPI gateway + REST endpoints
├── screener/            # Market screening engine (FA + TA filters)
├── valuation/           # Stock valuation & recommendation engine
├── data/vn/             # Vietnamese stock data layer (vnstock adapter)
├── journal/             # Recommendation tracking (SQLite/PostgreSQL)
├── backtest/            # Screener backtesting framework
├── config/              # YAML configs (screener, valuation, system)
├── frontend/            # Next.js 16 dashboard
├── tests/               # Unit + integration tests (273 tests)
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

## Tính năng Chính

- **Screener FA+TA**: Lọc tự động theo 15+ tiêu chí cơ bản + kỹ thuật + chất lượng
- **Định giá đa phương pháp**: DCF (non-bank), P/E relative, P/B, dividend yield, quality metrics
- **Khuyến nghị có giải thích**: BUY/SELL/HOLD + target price + reasoning + disclaimer
- **Config-driven**: Thay đổi filter thresholds via YAML, không cần sửa code
- **Persistent journal**: Track khuyến nghị + paper portfolio để validate edge
- **Backtest-able**: Chạy screener trên lịch sử, so sánh vs VN-Index
- **Dual persistence**: PostgreSQL (production) + SQLite (offline fallback)
- **Bank vs non-bank**: Separate valuation models cho ngân hàng vs công ty phi tài chính
- **Disclaimer everywhere**: "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư"
- **Docker ready**: Compose stack cho backend, frontend, PostgreSQL
- **CI/CD**: GitHub Actions build Docker image

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific modules
pytest tests/test_screener.py -v
pytest tests/test_valuation.py -v
pytest tests/test_backend_api.py -v

# With coverage
pytest tests/ --cov=screener --cov=valuation --cov=data/vn
```

**Status**: 273 tests passing, 7 skipped, ~35%–40% coverage (target: 80%+)

## Triết lý

> "Phân tích cơ bản là hiểu công ty. Định giá là kết nối số liệu với hiểu biết đó."

— *Value Investing Wiki*

## Deployment

### Docker Compose (Recommended)

```bash
# Start all services (backend, frontend, PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**Services:**
- Backend API: `http://localhost:8090`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

### Environment Variables

Create `.env`:
```
# Backend
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/advisory_db

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8090
```

### Database Setup

PostgreSQL (Docker):
```bash
docker run -d \
  --name advisory-postgres \
  -e POSTGRES_USER=advisor \
  -e POSTGRES_PASSWORD=advisory123 \
  -e POSTGRES_DB=advisory_db \
  -p 5432:5432 \
  -v ./data/postgres:/var/lib/postgresql/data \
  postgres:16-alpine
```

Or use cloud PostgreSQL (Supabase, Neon, AWS RDS).

### Manual Backend Start

```bash
# Development
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --reload

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api.main:app
```

### Manual Frontend Start

```bash
cd frontend
npm install
npm run dev      # Development
npm run build    # Build
npm run start    # Production
```

## License

MIT — Dùng cho mục đích cá nhân / nội bộ.
