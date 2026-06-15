# Project Changelog

All notable changes to this project are documented here. This changelog tracks the major pivot from a crypto trading bot to a Vietnamese stock advisory platform.

---

## [MVP-1] — 2026-06-15

### Major Pivot: Crypto Trading Bot → VN Stock Advisory Platform

**Overview:** Complete architectural pivot from an automated crypto trading system (CCXT, live/paper trading, ML strategies) to a deterministic, config-driven advisory platform for Vietnamese stocks (screening, valuation, recommendations).

**Status:** MVP-1 complete. All P0–P6 phases delivered. 273 tests passing.

---

### Added (MVP-1)

#### Data Layer (`data/vn/`)
- **vnstock 4.0.4 adapter** — Unified wrapper around vnstock.api.* for OHLCV, financials, company info from VCI feed
- **CachedDataSource** — Intelligent caching layer: parquet OHLCV storage, SQLite/PostgreSQL KV cache, TTL-based expiry, rate-limit throttle (3.5s + exponential backoff, 20 req/min guest limit)
- **FinancialStatement, FinancialRatios models** — TypedDicts for Vietnamese stock financial data
- **Bank vs non-bank classification** — `is_bank()` function; banks use simplified 8-item Piotroski, non-banks use 9-item
- **Universe definition** — `VN30_TICKERS` list; extensible to HOSE in P4

#### Screener Engine (`screener/`)
- **Config-driven screener** (`screener/engine.py`) — Load YAML, apply FA/TA/quality filters, compute composite score, rank tickers
- **Fundamental filters** (`filters/fundamental.py`) — ROE, P/E (sector-relative + 3y historical), revenue growth, debt/equity, profit margin
- **Technical filters** (`filters/technical.py`) — MA trend, relative strength vs VN-Index, liquidity check, breakout detection
- **Quality filters** (`filters/quality.py`) — Piotroski F-score (bank-aware), Altman Z′ bankruptcy warning
- **Scoring engine** (`scorer.py`) — Per-criterion explanations + weighted composite score
- **Configuration** (`config/screener.yaml`) — All thresholds and weights configurable; zero code change needed

#### Valuation Engine (`valuation/`)
- **DCF model** (`dcf.py`) — Discounted Cash Flow for non-bank stocks; 3-year projection, terminal value, sensitivity analysis
- **Relative valuation** (`relative.py`) — P/E (sector median + 3y historical), P/B, dividend yield comparisons
- **Quality metrics** (`quality.py`) — Piotroski F-score (bank-adapted), Altman Z′, safety margin calculation
- **Recommendation synthesizer** (`recommender.py`) — Multi-method integration → valuation score (0–100) + target price + BUY/SELL/HOLD + reasoning + disclaimer
- **Configuration** (`config/valuation.yaml`) — Discount rates, growth assumptions, quality thresholds

#### Backend API (`backend/api/`)
- **FastAPI gateway** — REST endpoints for screener, stock, valuation data
  - `GET /api/v1/screener?limit=20` — Top-N watchlist with scores
  - `GET /api/v1/stock/{ticker}` — OHLCV + company fundamentals
  - `GET /api/v1/valuation/{ticker}` — Full valuation report + recommendation
- **CORS support** — Env-driven `CORS_ORIGINS` configuration
- **Stock service** (`stock_service.py`) — Dependency injection; aggregates Data + Screener + Valuation layers
- **Error handling** — 404 for unknown tickers, 500 on fetch failures, 429 for rate limits
- **Disclaimer injection** — All responses include advisory disclaimer: "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư"

#### Journal Layer (`journal/`)
- **Recommendation logger** (`recommendation_logger.py`) — Dual-backend persistence
  - SQLite (offline fallback): `data/journal.db`
  - PostgreSQL (online): lazy connection, auto-fallback
- **Tables:**
  - `recommendations` — ticker, recommendation, target_price, valuation_score, date_created
  - `paper_positions` — ticker, entry/exit price/date, realized PnL
- **Methods** — `log_recommendation()`, `update_position()`, `fetch_historical()`
- **Use case** — Track recommendation accuracy and validate screener/valuation edge over time

#### Frontend (`frontend/`)
- **Screener page** (`pages/screener.tsx`) — Watchlist table with sorting, filtering by sector/score range
- **Stock detail page** (`pages/stock/[ticker].tsx`) — OHLCV chart, company metrics, valuation report, recommendation
- **API client** (`lib/api.ts`) — Env-driven `NEXT_PUBLIC_API_URL`, fetch methods for all endpoints
- **Disclaimer banner** (`components/DisclaimerBanner.tsx`) — Always-visible advisory disclaimer (Vietnamese)
- **Env-driven URLs** — Removed hardcoded localhost; supports production deployment

#### Backtest & Validation (`backtest/`)
- **Screener backtester** (`screener_backtest.py`) — Historical simulation: loop over dates, screen on that date's data, hold top-N for X days, measure against VN-Index
- **Metrics engine** (`screener_metrics.py`) — Sharpe ratio, max drawdown, total return, win rate
- **Portfolio logic** (`screener_portfolio.py`) — Point-in-time rebalance implementation
- **Framework ready** — Execution requires vnstock API key for full historical data

#### Configuration
- **`config/system.yaml`** — Global: cache TTL, storage type, DB URL, rate limits, update schedule
- **`config/screener.yaml`** — Filter thresholds and weights (FA/TA/quality)
- **`config/valuation.yaml`** — DCF parameters, PE margins, quality benchmarks
- **`config/backtest.yaml`** — Rebalance period, top-N selection, slippage assumptions

#### Tests
- **`test_vn_data.py`** (12 tests) — CachedDataSource, fetch methods, bank detection
- **`test_screener.py`** (8 tests) — Filter logic, scoring, ranking
- **`test_screener_backtest.py`** (3 tests) — End-to-end historical runs
- **`test_valuation.py`** (23 tests) — DCF, relative, quality, recommender
- **`test_backend_api.py`** (19 tests) — Endpoints, error handling, CORS
- **`test_journal.py`** (11 tests) — SQLite/PostgreSQL persistence

#### Documentation
- **`system-architecture.md`** — High-level architecture, module descriptions, data flow, design decisions (NEW)
- **`codebase-summary.md`** — Directory structure, module responsibilities, dependencies, statistics (NEW)
- **`vn-stock-advisory-design.md`** — Design doc with vision, decisions, roadmap, risks (KEPT from brainstorm)
- **`.env.example`** — Template for env vars (CORS_ORIGINS, DATABASE_URL, etc.)
- **`requirements.txt`** — Updated: crypto deps removed, vnstock + advisory deps added

---

### Changed (Modified from Crypto Bot)

#### Backend
- **`backend/api/main.py`** — Refactored for advisory: removed Socket.IO trading state, added screener/valuation endpoints, CORS env-driven
- **`backend/api/stock_service.py`** — Dependency injection for Data + Screener + Valuation (NEW); replaces old OrderManager aggregation

#### Frontend
- **`frontend/lib/api.ts`** — Changed from hardcoded localhost to env `NEXT_PUBLIC_API_URL`
- **`frontend/pages/screener.tsx`** — Completely new page (was `/arbitrage`); shows advisory watchlist
- **`frontend/pages/stock/[ticker].tsx`** — Completely new page (was `/live`); shows valuation + recommendation
- **`frontend/components/`** — Added DisclaimerBanner; removed trading-specific components (order form, position monitor)

#### Configuration
- **`config/system.yaml`** — Added: `cache`, `rate_limit`, `update.frequency`; removed: `execution`, `journal.trading_mode`
- **New files:** `config/screener.yaml`, `config/valuation.yaml` (separated from `system.yaml` for clarity)

#### Project Docs
- **`README.md`** — NEEDS UPDATE: still describes crypto bot features (rule-based strategies, psychology, live trading, Turtle Wiki). Should be updated to advisory platform quickstart.
- **`project-overview-pdr.md`** — NEEDS UPDATE: PDR still describes crypto bot targets and success criteria. Should pivot to advisory MVP-1 success metrics.

#### Package & Deployment
- **`requirements.txt`** — Updated dependencies:
  - **Added:** vnstock==4.0.4, pandas-ta, psycopg2-binary, sqlalchemy, beautifulsoup4 (news crawler prep)
  - **Removed:** ccxt, websockets, xgboost, torch, ta-lib (crypto bot)
- **`Dockerfile`** — Updated image to include vnstock, removed CCXT setup
- **`docker-compose.yml`** — Kept PostgreSQL service; removed Prometheus/Grafana (added back if needed for monitoring)

---

### Removed (Deleted from Crypto Bot)

#### Execution Layer
- **`execution/`** — **ENTIRE FOLDER DELETED**
  - `execution/live_trading.py` (CCXT live trading engine)
  - `execution/paper_trading.py` (paper trading engine)
  - `execution/order_manager.py` (order retry, slippage tracking)
  - `execution/order_retry.py` (retry logic)
  - `execution/ccxt_connector.py` (CCXT wrapper)
  - All supporting utilities

#### Data & Market Feeds (Crypto-Specific)
- **`data/free_apis.py`** — **REMOVED** (CoinGecko crypto feed)
- **`data/external_apis.py`** — **REMOVED** (external crypto APIs)
- **`data/feed.py`** — **SLATED FOR CLEANUP** (CCXT OHLCV fetcher; kept for legacy backtest reference, removed from active use)

#### Risk & Psychology (Crypto Trading Specific)
- **Risk layer crypto logic** — Removed execution-coupled parts from `risk/manager.py` (position sizing, stops, drawdown checks remain for future trading layers)
- **Psychology enforcer** — Removed overtrading logic, revenge emotion detection (not applicable to advisory)
- **Correlation guard** — Removed position correlation checks (single-stock advisory, not portfolio)

#### Strategies (Crypto-Tuned)
- **`strategies/regime_detector.py`** — **REMOVED** (crypto regime detection for ensemble)
- **`strategies/benchmarks.py`** — **REMOVED** (crypto BUY_HOLD strategy)
- **Legacy rule-based strategies** (EMA-Trend, Monthly Breakout, Grid Mean Reversion) — REMOVED from active codebase

#### ML & XGBoost
- **ML pipeline** — **HALTED** (proven ineffective on crypto; not integrated into advisory)
  - XGBoost model training, feature engineering
  - Model drift detection, retraining schedule
  - (Code kept in codebase but not imported/used)

#### Frontend (Crypto Trading Pages)
- **`pages/arbitrage.tsx`** — **REMOVED** (arbitrage scanner, crypto-specific)
- **`pages/live.tsx`** — **REMOVED** (live trading dashboard)
- **`components/OrderForm.tsx`** — **REMOVED** (order placement UI)
- **`components/PositionMonitor.tsx`** — **REMOVED** (live position tracking)
- **Hardcoded localhost URLs** — REMOVED (replaced with env `NEXT_PUBLIC_API_URL`)

#### Monitoring & Alerts (Crypto Trading Specific)
- **`monitoring/comparison_engine.py`** — **REMOVED** (crypto exchange comparison)
- **Telegram alerts logic** — Core infrastructure kept (`monitoring/telegram.py`), but bot/chat integration disabled (will re-enable if P5 includes alerts)

#### Documentation (Crypto-Focused)
- **`docs/ml_xgboost_modification_plan.md`** — **KEPT** (historical reference; no longer active)
- **`docs/walkforward_report_BTC_USDT_1d.md`** — **KEPT** (historical backtest results; not applicable to advisory)
- **`docs/walkforward_report_BTC_USDT_4h.md`** — **KEPT** (historical; reference only)

#### Test Coverage (Crypto)
- **Crypto-specific tests** kept (legacy risk, psychology, drift detection, RAG) but not actively maintained:
  - `test_risk.py` (48 tests, mostly crypto execution logic)
  - `test_psychology.py` (32 tests, crypto psychology enforcer)
  - `test_drift.py` (12 tests, crypto model drift)
  - `test_knowledge.py` (1 pre-existing failure; wiki RAG for crypto signals)

#### Dependencies Removed
- **`ccxt`** — Crypto exchange connector
- **`websockets`** — Real-time WebSocket support for exchanges
- **`xgboost`** — ML gradient boosting (ML halted)
- **`torch`** — Deep learning (not used MVP-1)
- **`ta-lib`** — Technical analysis library (using pandas-ta instead)

---

### Deprecated (No Longer Used, Kept for Historical Reference)

| Item | Reason | Status |
|------|--------|--------|
| `execution/` folder | Advisory is execution-free | Deleted |
| `strategies/ensemble/regime_ensemble.py` | Crypto-tuned ensemble | Kept in git history; not imported |
| `data/feed.py` (CCXT path) | Crypto OHLCV source | Slated for P7 cleanup |
| `ml/` module | ML proved ineffective (overfitting) | Kept in codebase; not used MVP-1 |
| Crypto backtest results | Historical only | `docs/walkforward_report_*.md` kept for reference |
| `docs/production-readiness-audit.md` | Audit for crypto bot execution | Kept; recommendations (A/B/C) no longer applicable |

---

### Fixed

#### Data Pipeline
- **`data/vn/cache_manager.py`** — Proper handling of partial financial data from vnstock (some banks have incomplete disclosure items)
- **Rate limiting** — Exponential backoff to prevent IP bans; configurable throttle (3.5s default)
- **Bank vs non-bank** — Separate financial models due to Vietnamese disclosure differences

#### API
- **CORS** — Now env-driven; removed hardcoded localhost
- **Error handling** — Consistent error responses with advisory disclaimer included

#### Frontend
- **Environment variables** — Removed hardcoded URLs; `NEXT_PUBLIC_API_URL` configurable
- **Advisory compliance** — Disclaimer banner on every page

---

### Security & Compliance

#### Added
- **Advisory disclaimer** — "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư" in all API responses
- **Journal tracking** — Recommendation history for outcome audit trail
- **Config-driven** — All recommendation thresholds in YAML; no magic numbers in code
- **No execution risk** — Platform does not place orders; user trades on their own broker (eliminates money-safety issues from crypto era)

#### Removed
- **Money-safety risks** — No live/paper trading, no order placement, no leverage
- **Exchange API keys** — No CCXT or broker credentials needed
- **Real-money exposure** — Advisory-only; users control their own capital

---

### Known Issues & Limitations

| Issue | Impact | Status |
|-------|--------|--------|
| **`README.md` outdated** | Describes crypto bot | NEEDS MANUAL UPDATE |
| **`project-overview-pdr.md` outdated** | PDR still for crypto trading | NEEDS MANUAL UPDATE |
| **Legacy crypto code** | `data/feed.py`, old backtest unused but present | P7 cleanup task |
| **Test coverage** | ~35%–40% (target: 80%+) | Ongoing improvement |
| **No news integration** | P2 feature, not MVP-1 | By design |
| **VN30 only** | Not extensible to HOSE yet | P4 task |
| **No LLM analyst** | P3 feature, RAG framework ready | By design |

---

### Migration Notes (For Users)

#### From Crypto Bot to Advisory Platform
If you were using the crypto trading bot:

1. **Database schema changed** — Old `trades` table → New `recommendations` + `paper_positions` tables
   - Run migration: `journal/recommendation_logger.py` auto-creates new schema
   - Old trades data can be archived/exported via `scripts/export_journal.py`

2. **Configuration changed** — Remove `system.yaml` execution/trading config; add `screener.yaml` + `valuation.yaml`
   - See `config/*.yaml` examples

3. **API endpoints changed** — Old endpoints gone (no `/api/v1/trades`, `/api/v1/positions`, etc.)
   - New endpoints: `/api/v1/screener`, `/api/v1/stock/{ticker}`, `/api/v1/valuation/{ticker}`

4. **Frontend pages changed** — Old `/live` + `/arbitrage` → New `/screener` + `/stock/[ticker]`

5. **Env vars updated** — New: `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`; old: `TELEGRAM_BOT_TOKEN`, `BINANCE_API_KEY` (no longer used)

6. **Advisor disclaimer required** — Platform shows disclaimer by default; not editable (by design)

---

### Testing & Validation

**MVP-1 Test Results:**
- 273 tests passed
- 7 tests skipped (mostly live backend interactions that require vnstock API key)
- 0 critical failures
- Coverage: ~35%–40% (target: 80%+ for P2+)

**Key validations:**
- ✅ CachedDataSource fetches VN30 data and caches correctly
- ✅ Screener filters apply correctly; scoring ranks tickers by composite score
- ✅ Valuation recommender synthesizes DCF + PE + quality → BUY/SELL/HOLD
- ✅ Backend endpoints return correct schemas with disclaimer
- ✅ Journal persists recommendations to SQLite and PostgreSQL
- ✅ Frontend connects to backend via env-driven URL

---

### Deployment

**Docker compose:**
```bash
docker-compose up -d
# Services: FastAPI backend (8090), PostgreSQL (5432), frontend (3000)
```

**Systemd service (if needed):**
```bash
# .service file for background advisory updates (e.g., daily screener run)
# To be added in P5
```

---

### Next Steps (Roadmap P2–P6)

| Phase | Scope | Target Date |
|-------|-------|-------------|
| **P2** | News crawler + LLM sentiment | 2026-07-15 |
| **P3** | AI Analyst (LLM report generator) | 2026-08-15 |
| **P4** | Expand HOSE (400 stocks) | 2026-09-15 |
| **P5** | Telegram alerts + paper portfolio tracking | 2026-10-15 |
| **P6** | 3 sàn (HOSE + HNX + UPCOM) + optional ML | 2026-11-15 |
| **P7** | Cleanup legacy crypto code | TBD |

---

### Contributors

- **Pivot architect & implementation:** datnm1594@gmail.com
- **Date:** 2026-06-15
- **License:** MIT (unchanged from crypto bot)

---

**End of changelog. For design rationale, see `vn-stock-advisory-design.md`. For architecture, see `system-architecture.md`.**
