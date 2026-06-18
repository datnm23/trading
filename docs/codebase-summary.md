# Codebase Summary — VN Stock Advisory Platform (MVP-1)

> **Last Updated:** 2026-06-15
> **Project:** Pivot from crypto trading bot → Vietnamese stock advisory platform
> **Status:** MVP-1 complete (P0–P6 phases, 273 tests passed)
> **Lines of Code:** ~6,275 Python + 1,200+ TypeScript/Frontend

---

## 1. Project Overview

**VN Stock Advisory Platform** is a deterministic, config-driven system for Vietnamese stock screening, valuation, and watchlist generation. It provides advisory recommendations (BUY/SELL/HOLD) anchored to fundamental analysis (DCF, P/E relative, quality metrics) and technical signals, with results tracked in a journal for outcome validation.

**Key characteristics:**
- **Advisory-only** (no execution, no orders)
- **Data-driven** (vnstock 4.0.4 with cached OHLCV + financials)
- **Config-centric** (screener/valuation logic via YAML, no code changes needed)
- **Backtest-able** (validate screener edge on historical data)
- **Multi-tier persistence** (PostgreSQL primary, SQLite fallback)

---

## 2. Directory Structure

```
trading/
├── backend/api/                 # FastAPI + Socket.IO gateway
│   ├── main.py                  # App init, CORS, health endpoint
│   ├── stock_service.py         # DI service: aggregates data+screener+valuation
│   ├── routers/                 # Endpoint implementations
│   │   ├── screener.py          # GET /api/v1/screener
│   │   ├── stock.py             # GET /api/v1/stock/{ticker}
│   │   └── valuation.py         # GET /api/v1/valuation/{ticker}
│   └── models.py                # Pydantic response schemas
│
├── data/                        # Market data pipeline (hybrid old/new)
│   ├── feed.py                  # Legacy crypto OHLCV fetcher (slated for cleanup)
│   ├── free_apis.py             # Legacy CoinGecko (REMOVED)
│   ├── external_apis.py         # Legacy external sources (REMOVED)
│   ├── vn/                      # NEW: Vietnamese stock data
│   │   ├── adapter.py           # vnstock.api.* wrapper
│   │   ├── models.py            # TypedDicts: FinancialStatement, Ratios, CompanyInfo
│   │   ├── data_fetcher.py      # Public API: fetch_ohlcv, fetch_financials, etc.
│   │   ├── cache_manager.py     # CachedDataSource: parquet + SQLite/PostgreSQL KV
│   │   └── universe.py          # VN30 ticker list + bank/non-bank classifier
│   ├── raw/                     # Raw market data (OHLCV, orders)
│   └── journal.db               # SQLite cache (offline fallback)
│
├── screener/                    # Market screening (NEW)
│   ├── engine.py                # Core screener: load config, run filters, rank
│   ├── scorer.py                # Composite scoring by weighted criteria
│   ├── filters/                 # Individual filter implementations
│   │   ├── fundamental.py       # ROE, P/E, revenue growth, debt/equity, margin
│   │   ├── technical.py         # MA trend, RS vs VN-Index, liquidity, breakout
│   │   └── quality.py           # Piotroski F, Altman Z′
│   └── config/                  # (See config/ for screener.yaml)
│
├── valuation/                   # Stock valuation & recommendations (NEW)
│   ├── dcf.py                   # Discounted Cash Flow (non-bank only)
│   ├── relative.py              # P/E relative, P/B, dividend yield
│   ├── quality.py               # Piotroski F-score, Altman Z′
│   ├── recommender.py           # Synthesize → score + target + BUY/SELL/HOLD
│   └── __init__.py
│
├── journal/                     # Recommendation & position tracking
│   ├── recommendation_logger.py # Dual-backend: SQLite + PostgreSQL
│   └── __init__.py
│
├── backtest/                    # Backtesting & validation
│   ├── screener_backtest.py     # Historical screener run & point-in-time rebalance
│   ├── screener_metrics.py      # Sharpe, max DD, total return, win rate
│   ├── screener_portfolio.py    # Rebalance logic
│   ├── engine.py                # Legacy backtest engine (crypto; kept for reference)
│   ├── run.py                   # CLI runner
│   └── __init__.py
│
├── frontend/                    # Next.js 16 dashboard
│   ├── lib/
│   │   └── api.ts               # API client: env-driven NEXT_PUBLIC_API_URL
│   ├── pages/
│   │   ├── index.tsx            # Home
│   │   ├── screener.tsx         # Watchlist table, filters
│   │   ├── stock/[ticker].tsx   # Stock detail: chart, valuation, recommendation
│   │   └── _app.tsx             # App wrapper, theme
│   ├── components/
│   │   ├── DisclaimerBanner.tsx # Always-visible advisory disclaimer
│   │   └── ...                  # Other UI components
│   ├── next.config.js           # Next.js config
│   ├── tsconfig.json            # TypeScript config
│   └── package.json             # Dependencies (removed: unused crypto libs)
│
├── config/                      # YAML configuration files
│   ├── system.yaml              # Global settings: cache TTL, rate limits, DB URL
│   ├── screener.yaml            # FA/TA filter weights and thresholds
│   ├── valuation.yaml           # Discount rates, growth assumptions, quality benchmarks
│   ├── backtest.yaml            # Backtest params: rebalance period, top-N, slippage
│   └── local.yaml               # Dev overrides
│
├── tests/                       # Unit + integration tests
│   ├── test_vn_data.py          # CachedDataSource, fetch methods, bank detection
│   ├── test_screener.py         # Filter logic, scoring, ranking (8 tests)
│   ├── test_screener_backtest.py # End-to-end historical screener (3 tests)
│   ├── test_valuation.py        # DCF, relative, quality, recommender (23 tests)
│   ├── test_backend_api.py      # Endpoints, error handling, CORS (19 tests)
│   ├── test_journal.py          # SQLite/PostgreSQL persistence (11 tests)
│   ├── test_risk.py             # Legacy risk layer (from crypto; kept)
│   ├── test_psychology.py       # Legacy psychology (from crypto; kept)
│   ├── test_drift.py            # Legacy drift detection (from crypto; kept)
│   ├── test_knowledge.py        # Legacy wiki RAG (from crypto; 1 pre-existing failure)
│   └── __init__.py
│
├── scripts/                     # Utility scripts
│   ├── spike_vnstock.py         # Quick vnstock test (P0 spike)
│   ├── analyze_project.py       # Code metrics
│   ├── run_paper_trade.py       # Legacy paper trading runner (REMOVED use)
│   └── ...                      # Other helpers
│
├── docs/                        # Documentation (THIS FOLDER)
│   ├── system-architecture.md   # Architecture overview (NEW)
│   ├── codebase-summary.md      # This file
│   ├── project-changelog.md     # MVP-1 pivot summary (NEW)
│   ├── vn-stock-advisory-design.md  # Design doc (reference)
│   ├── production-readiness-audit.md # Audit from crypto era (reference)
│   ├── code-standards.md        # Coding conventions
│   ├── project-overview-pdr.md  # PDR (NEEDS UPDATE to advisory)
│   └── ...                      # Other docs
│
├── knowledge_engine/            # Legacy RAG (kept for future P3 AI analyst)
│   ├── rag_engine.py            # ChromaDB + LLM (not used MVP-1)
│   └── __init__.py
│
├── crawl-wiki/                  # Wiki crawler (kept for anchor; value-investing concepts)
│   └── ...
│
├── execution/                   # REMOVED: Entire execution layer gone
│   # (CCXT, live/paper trading, order managers deleted)
│
├── .env.example                 # Env var template
├── requirements.txt             # Dependencies (crypto libs removed)
├── pyproject.toml               # Project metadata
├── pytest.ini                   # Pytest config
├── Dockerfile                   # Docker image (FastAPI + worker)
├── docker-compose.yml           # Multi-container setup
│
├── README.md                    # Repo root README (NEEDS UPDATE from crypto → advisory)
├── CLAUDE.md                    # Project rules (orchestration, development)
├── .gitignore                   # Git ignore patterns
└── .github/workflows/           # CI/CD (GitHub Actions)
    └── build.yml                # Docker build pipeline
```

---

## 3. Core Modules

### 3.1 Data Layer (`data/vn/`)

**Purpose:** Fetch, normalize, cache Vietnamese stock data.

| File | Responsibility |
|------|-----------------|
| `adapter.py` | vnstock.api.* wrapper; fetches OHLCV, financials, company info from VCI feed |
| `models.py` | TypedDicts for FinancialStatement, FinancialRatios, CompanyInfo, StockPrice |
| `data_fetcher.py` | Public API: `fetch_ohlcv()`, `fetch_financials()`, `fetch_company_info()` |
| `cache_manager.py` | CachedDataSource: parquet OHLCV storage, SQLite/PostgreSQL KV cache, TTL, rate-limit throttle (3.5s, 20 req/min guest limit, exponential backoff) |
| `financials_store.py` | FinancialsStore: PostgreSQL/SQLite dual-backend for financial statements; `set_shares()` stores authoritative issue_share, `get_shares()` retrieves for DCF calculations |
| `universe.py` | VN30 ticker list, bank vs non-bank classifier (`is_bank()`) |

**Key classes:**
- `CachedDataSource` — main entry point; lazy loads from vnstock, caches to parquet/SQLite/PostgreSQL
- `FinancialStatement`, `FinancialRatios` — models for financial data
- `VN30_TICKERS` — hardcoded list for MVP-1

**Bank detection:** Non-bank stocks use standard 9-item Piotroski + Altman Z′; banks use 8-item variant (no R&D, different accruals).

---

### 3.2 Screener (`screener/`)

**Purpose:** Config-driven filtering and ranking to identify watchlist candidates.

| File | Responsibility |
|------|-----------------|
| `engine.py` | Main screener: load config, apply filters, compute composite score, rank tickers |
| `scorer.py` | Score aggregation: per-criterion explanations + weighted composite |
| `filters/fundamental.py` | FA filters: ROE, P/E (vs sector median + 3y hist), revenue growth, debt/equity, profit margin |
| `filters/technical.py` | TA filters: MA trend, relative strength vs VN-Index, liquidity, breakout detection |
| `filters/quality.py` | Quality filters: Piotroski F-score (bank-aware), Altman Z′ |

**Output:** 
```python
{
  "VCB": {"score": 82.5, "details": {"roe": 0.18, "pe": 12.5, ...}},
  "VNM": {"score": 76.3, "details": {...}},
  ...
}
```

**Config-driven:** All thresholds in `config/screener.yaml`; zero code change needed.

---

### 3.3 Valuation (`valuation/`)

**Purpose:** Multi-method valuation, target price, BUY/SELL/HOLD recommendation.

| File | Responsibility |
|------|-----------------|
| `dcf.py` | DCF (non-bank only): firm value minus net debt → equity value; per-share via authoritative shares; per-sector WACC/terminal-growth from config |
| `relative.py` | Relative: P/E (sector/3y hist), P/B, dividend yield |
| `quality.py` | Quality: Piotroski F, Altman Z′, safety margin |
| `recommender.py` | Synthesize all → valuation score (0–100) + target + recommendation + reasons; degenerate gate: |upside|<2% → reliable=False → INSUFFICIENT |

**Output:**
```python
{
  "ticker": "VCB",
  "valuation_score": 72,
  "target_price": 95_000,
  "recommendation": "BUY",  # or SELL, HOLD, INSUFFICIENT
  "upside_pct": 0.15,
  "reliable": True,  # False if upside ±2% (degenerate) or no DCF/relative value
  "dcf_value": 98_000,
  "pe_ratio": 12.5,
  "pe_median_sector": 14,
  "f_score": 8,
  "reasons": ["Strong F-score", "P/E below sector median", ...],
  "disclaimer": "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư."
}
```

**Bank-aware:** Non-bank uses DCF + PE + quality; bank uses PE + relative + quality (no DCF).

---

### 3.4 Backend API (`backend/api/`)

**Purpose:** REST API to serve screener, stock, and valuation data.

| File | Responsibility |
|------|-----------------|
| `main.py` | FastAPI app, CORS (env: CORS_ORIGINS), middleware, health check |
| `stock_service.py` | Dependency injection: aggregates Data, Screener, Valuation; unified signal matrix (buy_upside ≥+8%, sell_upside ≤−15%); degenerate gate (±2% upside → INSUFFICIENT) |
| `routers/screener.py` | `GET /api/v1/screener?limit=20` |
| `routers/stock.py` | `GET /api/v1/stock/{ticker}` |
| `routers/valuation.py` | `GET /api/v1/valuation/{ticker}` (returns `reliable` flag for signal filtering) |
| `models.py` | Pydantic response schemas |

**Env vars:**
- `CORS_ORIGINS` — comma-separated allowed domains
- `DATABASE_URL` — PostgreSQL connection (optional; fallback to SQLite)
- `NEXT_PUBLIC_API_URL` — (frontend) API base URL

**Error handling:** 404 for unknown tickers, 500 for data fetch failures, 429 for rate limits.

---

### 3.5 Journal (`journal/`)

**Purpose:** Persist recommendations and paper portfolio for outcome tracking.

| File | Responsibility |
|------|-----------------|
| `recommendation_logger.py` | Dual-backend SQLite + PostgreSQL; tables: `recommendations`, `paper_positions` |

**Tables:**
- `recommendations` (id, ticker, recommendation, target_price, date_created, valuation_score)
- `paper_positions` (id, ticker, entry_price, entry_date, exit_price, exit_date, pnl, realized)

**Methods:**
- `log_recommendation(ticker, rec_dict)` — save valuation output
- `update_position(ticker, exit_price)` — mark position closed
- `fetch_historical(ticker, limit)` — query past recommendations

**Lazy connect:** Connects to DB on first write; fallback to SQLite if PostgreSQL unavailable.

---

### 3.6 Frontend (`frontend/`)

**Purpose:** Next.js 16 dashboard for screener, stock detail, watchlist.

| File | Responsibility |
|------|-----------------|
| `lib/api.ts` | API client; uses env `NEXT_PUBLIC_API_URL` |
| `pages/screener.tsx` | Watchlist: table, sort, filter by sector/score range |
| `pages/stock/[ticker].tsx` | Stock detail: chart (via Chart.js), fundamentals, valuation report |
| `components/DisclaimerBanner.tsx` | Always-visible advisory disclaimer (Vietnamese) |
| `pages/_app.tsx` | App wrapper, theme provider |

**Changes from crypto version:**
- Removed hardcoded `localhost:8090` → env-driven `NEXT_PUBLIC_API_URL`
- Removed `/arbitrage`, `/live` pages
- Added Vietnamese language support

---

### 3.7 Backtest (`backtest/`)

**Purpose:** Validate screener edge and valuation accuracy on historical data.

| File | Responsibility |
|------|-----------------|
| `screener_backtest.py` | Historical screener: loop over dates, screen on that date's data, hold top-N for X days |
| `screener_metrics.py` | Metrics: Sharpe, max DD, total return, win rate vs VN-Index |
| `screener_portfolio.py` | Point-in-time rebalance logic |

**Execution:** Manual run (framework ready, needs vnstock API key for full historical data).

---

## 4. Dependencies

### Python (Core)
```
fastapi           # REST API framework
uvicorn           # ASGI server
pydantic          # Data validation
pandas            # Data manipulation
polars            # Fast dataframes (alternative to pandas for large datasets)
pandas-ta         # Technical analysis indicators
vnstock==4.0.4    # Vietnamese stock data adapter
requests          # HTTP client
sqlalchemy        # ORM for PostgreSQL/SQLite
psycopg2-binary   # PostgreSQL adapter
chromadb          # Vector DB (for future AI analyst, MVP-1 unused)
openai            # LLM API (for future, MVP-1 unused)
beautifulsoup4    # HTML scraping (for future news crawler)
loguru            # Logging
pytest            # Testing
pytest-asyncio    # Async test support
ruff              # Linting
```

### Removed (Crypto Bot)
```
ccxt              # Crypto exchange connector (REMOVED)
websockets        # WebSocket for real-time (REMOVED)
xgboost           # ML model (REMOVED - halted due to overfitting)
torch             # Deep learning (REMOVED)
```

### Frontend
```
next              # React framework
react             # UI library
typescript        # Type safety
chart.js          # Charts
axios             # HTTP client
sass              # CSS preprocessing
```

---

## 5. Testing Overview

| Test File | Count | Coverage |
|-----------|-------|----------|
| `test_vn_data.py` | 12 | CachedDataSource, fetch methods, bank detection |
| `test_screener.py` | 8 | Filter logic, scoring, ranking |
| `test_screener_backtest.py` | 3 | End-to-end historical runs |
| `test_valuation.py` | 23 | DCF, relative, quality, recommender |
| `test_backend_api.py` | 19 | Endpoints, error handling, CORS |
| `test_journal.py` | 11 | SQLite/PostgreSQL persistence |
| `test_risk.py` | 48 | Legacy risk layer (from crypto) |
| `test_psychology.py` | 32 | Legacy psychology (from crypto) |
| `test_drift.py` | 12 | Legacy drift detection (from crypto) |
| `test_knowledge.py` | 1 | Legacy RAG (1 pre-existing failure) |
| **Total** | **273 passed, 7 skipped** | ~35%–40% (target: 80%+) |

**Running tests:**
```bash
pytest tests/ -v                   # All tests
pytest tests/test_screener.py -v   # Specific module
pytest tests/ -k "test_dcf" -v    # Match pattern
pytest tests/ --cov               # Coverage report
```

---

## 6. Configuration

### `config/system.yaml` (Global)
```yaml
cache:
  ttl_hours: 24
  storage: "parquet"  # or "sqlite"
  db_url: "postgresql://user:password@localhost:5432/advisory_db"

rate_limit:
  requests_per_minute: 20
  backoff_max_seconds: 60

update:
  frequency: "eod"  # end-of-day
  days: "mon-fri"
```

### `config/screener.yaml` (Screener Logic)
```yaml
filters:
  roe_min: 0.15
  pe_max: 15
  revenue_growth_min: 0.10
  debt_to_equity_max: 0.50

weights:
  roe: 0.25
  pe: 0.20
  growth: 0.20
  quality: 0.35
```

### `config/valuation.yaml` (Valuation Logic)
```yaml
dcf:
  discount_rate: 0.10
  growth_rate: 0.05
  terminal_growth: 0.02

pe:
  safety_margin: 0.20  # 20% below fair value

quality:
  f_score_min: 4  # out of 9 (non-bank)
  z_score_min: 1.8  # Altman warning threshold
```

---

## 7. Key Statistics

| Metric | Value |
|--------|-------|
| Python modules | 35+ |
| Test files | 10 |
| Test count | 273 passed, 7 skipped |
| Documented endpoints | 3 (screener, stock, valuation) |
| Config files | 4 (system, screener, valuation, backtest) |
| Frontend pages | 3 (home, screener, stock detail) |
| Supported stocks (MVP) | 30 (VN30) |
| Largest module | backend/api/main.py (~250 LOC) |
| Codebase age | Active development, 2026 |

---

## 8. Development Workflow

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Backend
```bash
# Development server (auto-reload)
uvicorn backend.api.main:app --host 0.0.0.0 --port 8090 --reload

# Production (gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api.main:app
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # Next.js dev server (localhost:3000)
npm run build  # Production build
npm run start  # Production server
```

### Tests
```bash
pytest tests/ -v
pytest tests/ --cov=screener --cov=valuation --cov=data/vn
```

### Docker
```bash
docker-compose up -d      # Start all services
docker-compose logs -f    # View logs
docker-compose down       # Stop services
```

---

## 9. Known Limitations & Future Work

| Item | Status | Note |
|------|--------|------|
| News crawler + LLM sentiment | 🔲 P2 | Not in MVP-1 |
| AI Analyst (LLM report) | 🔲 P3 | RAG infrastructure ready, not used MVP-1 |
| Expand HOSE (400 stocks) | 🔲 P4 | VN30 only for MVP-1 |
| Telegram alerts | 🔲 P5 | Infrastructure kept from crypto bot, not integrated advisory |
| Paper portfolio auto-rebalance | 🔲 P5 | Journal basic tracking only |
| TCBS/DNSE data adapters | 🔲 Future | vnstock primary for MVP-1 |
| Cleanup legacy crypto data | 🔲 P7 | `data/feed.py`, old backtest code slated for removal |
| Increase test coverage to 80%+ | 🔲 Ongoing | Currently ~35%–40% |

---

## 10. Known Issues

1. **Legacy crypto code still present** (not actively used MVP-1):
   - `data/feed.py` (OHLCV fetch from CCXT) — slated for P7 cleanup
   - `execution/` folder structure deleted but some helper utils may linger
   - Backtest engine has crypto-specific parameters (slippage, commission for crypto exchanges)

2. **PDR outdated:** `project-overview-pdr.md` still describes crypto bot; needs update to advisory scope

3. **README.md outdated:** Still references crypto bot features and quickstart (e.g., "Run backtest with rule-based strategy")

4. **Test coverage** (~35%–40%) — target 80%+; most gaps in frontend and backtest modules

5. **Production readiness audit** (`production-readiness-audit.md`) — audit for crypto bot, not advisory; recommendations (A/B/C) no longer fully applicable

---

## 11. File Naming Conventions

- **Modules:** `snake_case` (e.g., `data_fetcher.py`, `recommendation_logger.py`)
- **Classes:** `PascalCase` (e.g., `CachedDataSource`, `FinancialStatement`)
- **Functions/methods:** `snake_case` (e.g., `fetch_ohlcv()`, `log_recommendation()`)
- **Config files:** `snake_case.yaml` (e.g., `screener.yaml`, `system.yaml`)
- **Test files:** `test_*.py` (e.g., `test_screener.py`)

---

## 12. Contact & Contributions

**Project owner:** datnm1594@gmail.com (as of 2026-06-15)

**Key decision:** All changes to screener/valuation logic go through `config/*.yaml` files first. Code changes only if config is insufficient.

---

**End of codebase summary. For architecture details, see `system-architecture.md`. For design decisions, see `vn-stock-advisory-design.md`.**
