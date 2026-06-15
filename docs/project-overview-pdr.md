# Project Overview — PDR

## Product Development Requirements

### Tên sản phẩm
**VN Stock Advisory Platform (MVP-1)** — Nền tảng tư vấn chứng khoán Việt Nam cung cấp screening, định giá, và khuyến nghị có giải thích.

### Mục tiêu (MVP-1)
Xây dựng **nền tảng advisory deterministic, config-driven, backtest-able** cho thị trường chứng khoán Việt Nam:
1. **Screener** — Lọc tự động (FA+TA+quality) để tìm mã tiềm năng
2. **Valuation** — Định giá đa phương pháp (DCF, P/E relative, quality) + target price
3. **Recommendation** — BUY/SELL/HOLD + khuyến nghị có giải thích + disclaimer
4. **Journal** — Track khuyến nghị + paper portfolio để validate edge

### Target Users
- Nhà đầu tư cá nhân muốn rà soát thị trường VN tự động
- Value investors cần định giá khoa học + benchmark vs ngành
- Retail traders muốn validate screener edge trước khi live trade
- Quant traders building advisory layer cho nền tảng của họ

### Key Differentiators
- **Multi-method valuation**: DCF (non-bank) + relative (P/E sector) + quality (F-score) → diversified edge
- **Bank-aware models**: Separate valuation logic cho ngân hàng vs non-bank (khác schema BCTC)
- **Config-driven screening**: Thay đổi filter thresholds via YAML, zero code change
- **Outcome tracking**: Journal tracks every recommendation + paper portfolio → measure recommendation accuracy over time
- **Advisory disclaimer everywhere**: "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư" — transparency first
- **Backtest-able**: Validate screener edge on historical data; compare vs VN-Index

## System Requirements (MVP-1)

### Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| F1 | Fetch OHLCV + financials từ vnstock API | P0 | ✅ Done |
| F2 | CachedDataSource (parquet + SQLite/PostgreSQL KV) | P0 | ✅ Done |
| F3 | Screener with FA filters (ROE, P/E, growth, debt, margin) | P0 | ✅ Done |
| F4 | Screener with TA filters (MA trend, RS vs Index, liquidity) | P0 | ✅ Done |
| F5 | Screener with quality filters (Piotroski F, Altman Z′) | P0 | ✅ Done |
| F6 | DCF valuation (non-bank only) | P0 | ✅ Done |
| F7 | Relative valuation (P/E sector, P/B, div yield) | P0 | ✅ Done |
| F8 | Quality scoring (Piotroski F, Altman Z′, safety margin) | P0 | ✅ Done |
| F9 | Recommendation synthesizer (score 0–100 + target + reasoning) | P0 | ✅ Done |
| F10 | Bank vs non-bank detection + separate models | P0 | ✅ Done |
| F11 | FastAPI backend endpoints (/screener, /stock, /valuation) | P0 | ✅ Done |
| F12 | CORS env-driven + advisory disclaimer in responses | P0 | ✅ Done |
| F13 | Next.js frontend (Screener page, Stock detail page) | P0 | ✅ Done |
| F14 | Frontend API client (env NEXT_PUBLIC_API_URL) | P0 | ✅ Done |
| F15 | Recommendation journal (SQLite/PostgreSQL) | P0 | ✅ Done |
| F16 | Paper positions tracker (entry/exit, realized PnL) | P0 | ✅ Done |
| F17 | Screener historical backtest (point-in-time rebalance) | P0 | ✅ Done |
| F18 | Screener metrics (Sharpe, max DD, total return, win rate) | P0 | ✅ Done |
| F19 | Config-driven screener (YAML thresholds + weights) | P0 | ✅ Done |
| F20 | Config-driven valuation (YAML DCF params, quality benchmarks) | P0 | ✅ Done |

### Non-Functional Requirements (MVP-1)

| ID | Requirement | Target |
|----|-------------|--------|
| NF1 | API latency | < 2s for /screener, /stock, /valuation endpoints |
| NF2 | Cache hit rate | 90%+ on OHLCV/financials fetches |
| NF3 | Rate limit handling | Graceful backoff when vnstock limit hit (20 req/min) |
| NF4 | Test coverage | 80%+ (current: ~35%–40%; P2+ goal) |
| NF5 | Config-driven | All filter thresholds + valuation params in YAML |
| NF6 | Data consistency | Screener and valuation use same data snapshot |
| NF7 | Persistence | Recommendations + paper positions survive restart |
| NF8 | Disclaimer compliance | "Chỉ mang tính tham khảo..." in every API response |
| NF9 | Scalability | Support HOSE (400 stocks) in P4 without refactor |
| NF10 | Observability | Log screener runs, valuation computations, errors |

## Architecture Summary (MVP-1)

### High-Level Diagram

```
Frontend (Next.js)
├─ Screener page
└─ Stock detail page
         │
         ▼
Backend API (FastAPI)
├─ GET /api/v1/screener
├─ GET /api/v1/stock/{ticker}
└─ GET /api/v1/valuation/{ticker}
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
Screener  Valuation  Journal
(FA+TA)   (DCF+PE)  (SQLite/PG)
    │         │
    └────┬────┘
         │
    Data Layer (vnstock adapter)
         │
    CachedDataSource (parquet + KV cache)
```

### Data Flow

1. **User visits Screener page** → Frontend calls GET /api/v1/screener
2. **Backend** loads config/screener.yaml, calls screener.run()
3. **Screener** fetches OHLCV + financials (cached), applies filters, scores tickers
4. **Backend** ranks, returns top-20 watchlist with composite scores
5. **User clicks stock** → Frontend calls GET /api/v1/stock/{ticker} + GET /api/v1/valuation/{ticker}
6. **Backend** aggregates data, runs valuation, synthesizes recommendation
7. **Journal** logs recommendation (ticker, score, target, date)
8. **Backend** returns response with disclaimer
9. **Frontend** displays chart, metrics, recommendation with warning banner

## Success Criteria (MVP-1)

### Functional Validation
- ✅ Screener runs on VN30, identifies 5–15 candidates per run
- ✅ Valuation provides meaningful target prices (±20% accuracy acceptable MVP)
- ✅ Recommendations track-able: can measure % correct over time
- ✅ All API endpoints respond < 2s with correct schemas
- ✅ Frontend connects successfully to backend
- ✅ Journal persists to SQLite and PostgreSQL correctly

### Test Results
- ✅ 273 tests passing, 7 skipped
- ✅ Zero critical failures
- ✅ Coverage ~35%–40% (P2+ goal: 80%+)

### Launch Readiness
- ✅ Screener + valuation logic frozen (ready for P2 news/AI)
- ✅ Backend API stable, CORS env-driven
- ✅ Frontend accessible, mobile-responsive (P2 enhancement)
- ✅ Disclaimer visible everywhere
- ✅ Docker compose stack working

## Tech Stack (MVP-1)

| Category | Technology |
|----------|-----------|
| **Language** | Python 3.11+ |
| **Data source** | vnstock 4.0.4 (VCI) |
| **Data processing** | pandas, polars, pandas-ta |
| **Storage** | parquet (OHLCV), SQLite/PostgreSQL (KV cache + journal) |
| **API** | FastAPI, uvicorn |
| **Frontend** | Next.js 16, TypeScript, Chart.js |
| **Testing** | pytest, pytest-asyncio |
| **Linting** | ruff |
| **Docker** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

**Optional (for P2+):**
- ChromaDB (vector DB for news RAG)
- OpenAI API (LLM analyst)
- beautifulsoup4 (news crawler)
- TCBS/DNSE adapters (data enrichment)

## Project Structure (MVP-1)

```
vn-stock-advisory/
├── backend/api/           # FastAPI gateway + REST endpoints
├── screener/              # Screening engine (FA + TA filters)
├── valuation/             # Valuation + recommendation
├── data/vn/               # Vietnamese stock data (vnstock adapter)
├── journal/               # Recommendation tracking
├── backtest/              # Screener backtesting framework
├── config/                # YAML configs (system, screener, valuation, backtest)
├── frontend/              # Next.js 16 dashboard
├── tests/                 # Unit + integration tests
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── requirements.txt       # Python dependencies
```

## Risks & Mitigations (MVP-1)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| vnstock API data incomplete/stale | Medium | High | Spike testing (P0 done); adapter abstraction for TCBS/DNSE swap |
| DCF assumptions unrealistic → sai định giá | Medium | High | Sensitivity analysis; prioritize relative valuation; wiki anchor to avoid value trap |
| LLM hallucination future (P3) | Medium | Medium | RAG strict context; force source citation; data from layer, LLM explains only |
| Filter overfitting on VN30 history | Medium | Medium | Walk-forward backtest; validate on unseen future data; monitor recommendation accuracy |
| Recommendation wrong → user loss | Medium–High | High | Disclaimer everywhere; track outcomes; show historical accuracy |
| User misinterprets "advisory" as guaranteed | Low–Medium | High | Disclaimer in 3 places: UI banner, API response, every email |
| Database data loss | Low | High | PostgreSQL backup; SQLite local cache fallback |
| Scaling to HOSE too complex | Low | Medium | Modular design; tested on VN30 subset first |

## Phase Status (MVP-1 = P0–P1 Complete)

| Phase | Scope | Status | Target |
|-------|-------|--------|--------|
| **P0** | Spike vnstock; remove execution layer | ✅ Done | 2026-06-01 |
| **P1 (MVP-1)** | Data+Screener+Valuation+API+FE+Journal | ✅ Done | 2026-06-15 |
| **P2** | News crawler + LLM sentiment | 🔲 Not started | 2026-07-15 |
| **P3** | AI Analyst (LLM report) | 🔲 Not started | 2026-08-15 |
| **P4** | Expand HOSE (400 stocks) | 🔲 Not started | 2026-09-15 |
| **P5** | Telegram alerts + paper tracking | 🔲 Not started | 2026-10-15 |
| **P6** | 3 sàn (HOSE+HNX+UPCOM) + optional ML | 🔲 Not started | 2026-11-15 |

## Glossary

| Term | Definition |
|------|------------|
| Screener | Automated filter to identify candidate stocks |
| Valuation | Multi-method assessment (DCF, P/E, quality) → target price |
| Recommendation | BUY/SELL/HOLD + reasoning + target price |
| Advisory-only | No execution, no orders; user trades on their broker |
| Disclaimer | "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư" |
| FA | Fundamental Analysis: financial metrics, growth, profitability |
| TA | Technical Analysis: price momentum, trends, support/resistance |
| DCF | Discounted Cash Flow: intrinsic value via cash flow projections |
| P/E | Price-to-Earnings ratio: relative valuation vs sector/history |
| F-score | Piotroski F-score: 9-point quality metric (8 for banks) |
| Z-score | Altman Z-score: bankruptcy risk indicator |
| Journal | Recommendation tracking + outcome history |
| Paper portfolio | Virtual portfolio tracking recommendation accuracy |
