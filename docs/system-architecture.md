# System Architecture — VN Stock Advisory Platform (MVP-1)

> **Status:** MVP-1 Complete (P0–P6 phases done, 273 tests passed)
> **Vision:** Advisory-only platform for Vietnamese stock screening, valuation, and watchlist management
> **Data:** vnstock 4.0.4 adapter (VCI source) with PostgreSQL/SQLite KV cache and parquet OHLCV storage
> **Scope:** VN30 (30 stocks), extensible to HOSE (~400 stocks) in P4

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│             FRONTEND (Next.js 16)                   │
│  Screener │ Stock Detail │ Watchlist │ News Radar   │
└─────────────────────────────────────────────────────┘
                         ▲
                         │ Socket.IO / REST
                         │
┌─────────────────────────────────────────────────────┐
│         BACKEND API (FastAPI, uvicorn)              │
│ GET /api/v1/screener                               │
│ GET /api/v1/stock/{ticker}                         │
│ GET /api/v1/valuation/{ticker}                     │
│ CORS: env-driven CORS_ORIGINS                      │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    ┌────────┐    ┌──────────────┐  ┌──────────┐
    │ SCREEN │    │   ANALYSIS   │  │  JOURNAL │
    │  (FA+  │    │ + VALUATION  │  │  (Paper  │
    │   TA)  │    │ (DCF/PE/PB)  │  │Portfolio)│
    └────────┘    └──────────────┘  └──────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                  ▼
   ┌──────────────┐            ┌────────────────┐
   │  DATA LAYER  │            │ BACKTEST & VAL │
   │  (vnstock)   │            │  (screener     │
   │  + CachedDS  │            │   metrics)     │
   └──────────────┘            └────────────────┘
        │
   PostgreSQL / SQLite (KV cache + parquet OHLCV)
```

---

## 2. Core Modules

### 2.1 Data Layer (`data/vn/`)

**Purpose:** Fetch, normalize, and cache Vietnamese stock data from vnstock 4.0.4.

#### Files
- **`adapter.py`** — vnstock.api.* wrapper; handles VCI feeds (OHLCV, financials, company info)
- **`models.py`** — TypedDicts: FinancialStatement, FinancialRatios, CompanyInfo, StockPrice
- **`data_fetcher.py`** — Public API: `fetch_ohlcv()`, `fetch_financials()`, `fetch_ratios()`, `fetch_company_info()`
- **`cache_manager.py`** — `CachedDataSource`: parquet OHLCV, SQLite/PostgreSQL KV store, TTL, rate-limit throttle (3.5s + exponential backoff)
- **`financials_store.py`** — `FinancialsStore`: PostgreSQL/SQLite persistence for financial statements; `set_shares()`/`get_shares()` for authoritative shares-outstanding
- **`universe.py`** — VN30 ticker list; bank vs non-bank classification

#### Rate Limiting & Resilience
- Guest limit: 20 req/min per IP
- Backoff: exponential, max 60s
- Cache TTL: configurable per data type

#### Shares Outstanding (Authoritative)
- **`vn_shares` table** in `financials_store` stores issue_share (shares outstanding) from vnstock
- Collector script (`scripts/collect_vn30_financials.py`) populates via `set_shares(ticker, issue_share)`
- DCF/valuation prefers `get_shares()` from DB, falls back to company.issue_share
- Fixes Market Cap, P/B, and per-share DCF valuations with authoritative values

#### Bank vs Non-Bank Handling
- **Bank financial schemas differ** from non-bank (less detailed balance sheet items)
- `is_bank()` check → swap ratio/DCF models accordingly

---

### 2.2 Screener (`screener/`)

**Purpose:** Config-driven market scanning via FA + TA filters to identify watchlist candidates.

#### Files
- **`engine.py`** — Core screener: load config, run filters, rank results by composite score
- **`filters/`** — Individual filter implementations
  - `fundamental.py` (ROE, P/E, revenue growth, debt/equity, profit margin)
  - `technical.py` (MA trend, relative strength vs VN-Index, liquidity, breakout)
  - `quality.py` (Piotroski F, Altman Z′)
- **`scorer.py`** — Composite scoring (weighted per-criterion)
- **`config/screener.yaml`** — User-configurable thresholds and weights

#### Output
- Ranked watchlist (dict): ticker → composite score + per-criterion explanations

#### Backtest
- `backtest/screener_backtest.py` — Point-in-time rebalance top-N vs VN-Index
- `backtest/screener_metrics.py` — Sharpe, max drawdown, total return
- `backtest/screener_portfolio.py` — Rebalance portfolio logic

---

### 2.3 Valuation (`valuation/`)

**Purpose:** Multi-method valuation and BUY/SELL/HOLD recommendation with target price.

#### Files
- **`dcf.py`** — Discounted Cash Flow (non-bank only); firm value minus net debt equals equity value; per-share via authoritative shares-outstanding; terminal growth per sector (config override)
- **`relative.py`** — Relative valuation: P/E (vs sector median + 3y historical), P/B, dividend yield
- **`quality.py`** — Quality metrics: Piotroski F-score (banks: 8 items; non-banks: 9), Altman Z′ (bankruptcy warning)
- **`recommender.py`** — Synthesize methods → valuation score (0–100) + target price + BUY/SELL/HOLD + reasons; degenerate gate: upside within ±2% of current price → `reliable=False` → INSUFFICIENT recommendation

#### Config
- `config/valuation.yaml` — Discount rates (default WACC 0.13), growth assumptions (default terminal 0.03), quality thresholds, per-sector WACC/terminal-growth overrides under `dcf.sector_wacc`

#### Output
```python
{
  "ticker": "VCB",
  "valuation_score": 72,
  "target_price": 95_000,
  "recommendation": "BUY",  # or SELL, HOLD, INSUFFICIENT
  "upside_pct": 0.15,  # (target - current) / current; None if no reliable target
  "reliable": True,  # False if upside ±2% (degenerate) or no DCF/relative value
  "dcf_value": 98_000,
  "pe_ratio": 12.5,
  "pe_median_sector": 14,
  "f_score": 8,
  "reasons": ["Strong F-score", "P/E below sector median", ...]
}
```

---

### 2.4 Backend API (`backend/api/`)

**Purpose:** Serve screener, stock, and valuation data to frontend via REST + Socket.IO.

#### Files
- **`main.py`** — FastAPI app initialization, CORS (env: CORS_ORIGINS)
- **`stock_service.py`** — Dependency injection; aggregates Data, Screener, Valuation; unified signal matrix with tightened thresholds (`buy_upside` 0.0→0.08, `sell_upside` ≤−0.15)
- **Endpoints:**
  - `GET /api/v1/screener?limit=20` → top-N watchlist
  - `GET /api/v1/stock/{ticker}` → OHLCV + company info + latest metrics
  - `GET /api/v1/valuation/{ticker}` → full valuation report (includes `reliable` flag for signal filtering)
- **Responses:** Include advisory disclaimer: "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư"
- **Signal matrix:** BUY only when upside ≥+8% AND reliable=True; degenerate valuations (±2% upside) → INSUFFICIENT instead of false signals
- **Error handling:** 404 if ticker not in universe, 500 on data fetch failure

---

### 2.5 Journal (`journal/`)

**Purpose:** Track recommendations and paper portfolio outcomes.

#### Files
- **`recommendation_logger.py`** — Dual-backend: SQLite (offline) + PostgreSQL (online)
  - Tables: `recommendations` (ticker, recommendation, target_price, date), `paper_positions` (track paper portfolio entry/exit)
  - Methods: `log_recommendation()`, `update_position()`, `fetch_historical()`
- **Lazy connection:** Connect to DB on first write, fallback to SQLite if offline

#### Use Case
- Log each screener run and valuation recommendation
- Track paper portfolio entry/exit to measure recommendation accuracy over time
- Queryable history for backtesting and performance review

---

### 2.6 Frontend (`frontend/`)

**Purpose:** Next.js 16 dashboard for screener, stock detail, watchlist.

#### Files
- **`lib/api.ts`** — API client: env `NEXT_PUBLIC_API_URL`, fetch methods
- **`pages/screener.tsx`** — Watchlist table, filterable by sector/score
- **`pages/stock/[ticker].tsx`** — Stock detail: chart, valuation report, recommendation
- **`components/DisclaimerBanner.tsx`** — Always-visible disclaimer

#### Changes from Crypto Version
- Removed hardcoded `localhost:8090` URLs → use env `NEXT_PUBLIC_API_URL`
- Removed arbitrage and live trading pages
- Added Vietnamese text support

---

### 2.7 Backtest & Metrics (`backtest/`)

**Purpose:** Validate screener edge and valuation accuracy.

#### Files
- **`screener_backtest.py`** — Historical screener run: loop over dates, screen on that date's data, hold top-N for X days
- **`screener_metrics.py`** — Compute Sharpe, max DD, total return, win rate vs VN-Index
- **`screener_portfolio.py`** — Point-in-time rebalance logic
- **Execution:** Manual run (framework done, needs vnstock API key for live data)

---

## 3. Data Flow

```
User visits Screener page
    │
    ├─→ Frontend: GET /api/v1/screener
    │       │
    │       ├─→ Backend: screener.run()
    │       │       │
    │       │       ├─→ Data: fetch_ohlcv(), fetch_financials() (cached)
    │       │       │
    │       │       ├─→ Filters: fundamental, technical, quality
    │       │       │
    │       │       └─→ Scorer: composite_score per ticker
    │       │
    │       └─→ Backend: rank, return top-20
    │
    └─→ Frontend: Display watchlist

User clicks on ticker
    │
    ├─→ Frontend: GET /api/v1/stock/{ticker}
    │       │
    │       ├─→ Backend: aggregates OHLCV + company info
    │       │
    │       └─→ Returns chart data + fundamentals
    │
    └─→ Frontend: Display stock chart + metrics

User scrolls to valuation section
    │
    ├─→ Frontend: GET /api/v1/valuation/{ticker}
    │       │
    │       ├─→ Backend: valuation.recommend()
    │       │       │
    │       │       ├─→ Valuation: DCF, PE relative, quality scores
    │       │       │
    │       │       └─→ Return score + target + recommendation + reasons
    │       │
    │       └─→ Backend: log to journal
    │
    └─→ Frontend: Display valuation report + BUY/SELL/HOLD
```

---

## 4. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Data source** | vnstock (free) | No API key required, VCI feed reliable, extensible to TCBS/DNSE |
| **Cache strategy** | Parquet (OHLCV) + SQLite/PostgreSQL (KV) | Fast reads, partitionable, offline fallback |
| **Update frequency** | EOD daily | Advisory doesn't need intraday; cheaper, simpler |
| **Scope** | VN30 MVP, expandable | Manageable data, clean financials, easy validation |
| **Bank vs non-bank** | Separate DCF/ratio models | Vietnamese bank disclosures differ significantly |
| **Persistence** | PostgreSQL (preferred) + SQLite fallback | Journal tables for recommendations + paper positions |
| **Valuation method** | DCF + relative + quality | Anchored to wiki value-investing principles; multiple methods reduce single-method risk |
| **Advisory-only** | No execution, no orders | Eliminates money-safety risks; users trade on their broker |
| **Recommendation validity** | Disclaimer + track outcomes | Transparency: "tham khảo" + historical accuracy tracking |

---

## 5. Removed Components (from Crypto Bot)

**Execution layer:**
- `execution/` (CCXT, live/paper trading, order manager) — **completely removed**

**Crypto data & strategies:**
- `data/free_apis.py` (CoinGecko) — **removed**
- `data/external_apis.py` (crypto exchanges) — **removed**
- `data/feed.py` (crypto OHLCV) — **slated for cleanup** (backtest/ML legacy code still references; removed in P7)
- `strategies/regime_detector.py`, `strategies/benchmarks.py` (crypto-tuned) — **removed** (ML/backtest legacy)

**Frontend:**
- `pages/arbitrage`, `pages/live` — **removed**
- Hardcoded localhost URLs — **replaced with env-driven `NEXT_PUBLIC_API_URL`**

**Dependencies removed:**
- `ccxt`, `websockets`, `xgboost`, `torch` — **not in requirements.txt MVP-1**

---

## 6. Persistence Layer

### PostgreSQL (Recommended for Production)
```
Database: trading_journal (or advisory_db)
Tables:
  - recommendations (ticker, recommendation, target_price, date_created, confidence_score)
  - paper_positions (ticker, entry_price, entry_date, exit_price, exit_date, pnl, realized)
  - user_watchlist (ticker, added_date, notes)
```

### SQLite (Fallback for Offline)
- Same schema, file: `data/journal.db`
- Auto-created on first write
- Used when PostgreSQL unavailable

### Env vars
- `DATABASE_URL`: PostgreSQL connection string (optional; auto-fallback to SQLite)
- Example: `postgresql://user:password@localhost:5432/advisory_db`

---

## 7. Config-Driven Behavior

All thresholds configurable without code change:

- **`config/screener.yaml`** — FA/TA filter weights and thresholds
- **`config/valuation.yaml`** — Discount rates, growth assumptions, quality benchmarks
- **`config/system.yaml`** — Global settings: update schedule, cache TTL, rate limits

Example (screener.yaml):
```yaml
filters:
  roe_min: 0.15
  pe_max: 15
  revenue_growth_min: 0.10
  debt_to_equity_max: 0.50
  liquidity_min: 1_000_000_000  # VND

weights:
  roe: 0.25
  pe: 0.20
  growth: 0.20
  quality: 0.35
```

---

## 8. Testing Strategy

### Unit Tests (`tests/`)
- **`test_vn_data.py`** — CachedDataSource, fetch methods, bank detection
- **`test_screener.py`** — Filter logic, scoring, ranking
- **`test_valuation.py`** — DCF, relative, quality models, recommendation synthesis
- **`test_backend_api.py`** — Endpoint responses, error handling, CORS
- **`test_journal.py`** — SQLite/PostgreSQL persistence

### Integration Tests
- **`test_screener_backtest.py`** — End-to-end screener on historical data

### Coverage
- Target: 80%+
- Current: 273 tests passed, 7 skipped (mostly on live backend interactions)

---

## 9. Disclaimer & Compliance

**Every response includes:**
```
"disclaimer": "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư. 
Nhà đầu tư tự chịu trách nhiệm với quyết định giao dịch của mình."
```

**Journal tracks recommendations** to measure historical accuracy and validate edge.

---

## 10. Roadmap Status

| Phase | Scope | Status |
|-------|-------|--------|
| **P0** | Spike vnstock; remove execution layer | ✅ Done |
| **P1 (MVP-1)** | Data + Screener + Valuation + Endpoints + FE | ✅ Done |
| **P2** | News crawler + LLM sentiment | 🔲 Not started (P2 phase) |
| **P3** | AI Analyst (LLM report) | 🔲 Not started (P3 phase) |
| **P4** | Expand HOSE (~400 stocks) | 🔲 Not started (P4 phase) |
| **P5** | Telegram alerts + full paper tracking | 🔲 Not started (P5 phase) |

---

## 11. Unresolved Questions (Carry from Design)

1. **LLM provider for P3:** OpenAI (already available) vs local/Vietnamese-tuned model?
2. **Wiki expansion:** Keep Turtle Trading wiki or crawl Vietnamese value-investing sources?
3. **TCBS/DNSE integration:** When to add TCBS/DNSE adapters (P2/P3)?
4. **Paper portfolio tracking:** Current journal basic; expand with auto-rebalance simulation?
5. **Update schedule:** Daily EOD sufficient, or consider intraday for breakout/news-driven screening?
