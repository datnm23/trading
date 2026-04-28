---
title: "Remaining Features — Paper Monitor, Docker Frontend, Tests, CI Fixes"
description: "Plan to close all gaps: graduation monitoring, nginx static frontend, frontend test framework, DB test CI fixes, and remote push."
status: pending
priority: P1
effort: 8h
branch: main
tags: [graduation, docker, nginx, testing, ci-cd, frontend-tests]
created: 2026-04-28
---

# Plan: Remaining Features & Operational Gaps

## Context

All major phases A–F are complete (safety fixes, frontend pages, strategy tests, API tests, RAG, DevOps). The system has **119 passing tests**, **0 TODOs**, and a working static export build. However, 5 gaps remain before the system is operationally ready for 30-day paper trading graduation.

---

## G1: Paper Trading Graduation Monitor (P1 — 3h)

### Problem
The graduation criteria (30 days profitable, max DD < 10%, Sharpe > 0.5, winrate > 40%) are documented but not tracked in real-time. The user cannot see progress toward live trading approval.

### Data Flow
```
trades DB → /api/v1/trades?start_date=30d_ago
  → backend/graduation.py (compute metrics)
  → GET /api/v1/graduation
  → frontend /graduation page
  → display: days remaining, current stats, gate status
```

### Deliverables
1. **Backend** (`backend/api/graduation_service.py`):
   - Query last 30 days of trades from PostgreSQL
   - Compute: total return %, max drawdown, Sharpe ratio, winrate
   - Return `{days_traded, return_pct, max_drawdown, sharpe, winrate, gates: {return: bool, dd: bool, sharpe: bool, winrate: bool}, approved: bool}`
2. **API endpoint** (`backend/api/main.py`):
   - `GET /api/v1/graduation`
3. **Frontend page** (`frontend/app/graduation/page.tsx`):
   - Progress bars for each metric vs. threshold
   - Days remaining counter
   - Green/red gate indicators
   - "Not yet approved" / "Ready for live" banner
4. **Aggregator** (`backend/api/aggregator.py`):
   - Add graduation stats to SocketIO state broadcast

### Test Matrix
| Layer | What | How |
|-------|------|-----|
| Unit | graduation_service.compute_metrics() with fake trades | pytest |
| Integration | GET /api/v1/graduation | httpx + mock DB |
| E2E | /graduation page renders progress bars | manual build check |

### Risk: Low
- Pure read-only query, no trading logic
- Mitigation: mock trades in tests, verify edge cases (empty history, exactly 30 days, negative P&L)

### Rollback
- Remove route + page, no data migration needed

---

## G2: Docker Multi-Stage — Nginx Static Frontend (P2 — 2h)

### Problem
Current `docker-compose.yml` runs `npm run dev` for frontend. This is wasteful: uses Node.js dev server in production, no CDN benefit, consumes more RAM.

### Data Flow
```
frontend source → npm run build → dist/ (static HTML/CSS/JS)
  → nginx container (alpine, ~5MB) serves dist/
  → no Node.js runtime in production
```

### Deliverables
1. **Frontend Dockerfile** (`frontend/Dockerfile`):
   - Stage 1: `node:20-alpine` → build static files
   - Stage 2: `nginx:alpine` → serve `dist/` on port 80
   - `COPY nginx.conf /etc/nginx/conf.d/default.conf`
2. **Nginx config** (`frontend/nginx.conf`):
   - SPA fallback: `try_files $uri $uri.html $uri/ /index.html`
   - Gzip compression for JS/CSS
   - Cache headers for `_next/static/`
3. **docker-compose.yml** update:
   - Replace `frontend` service with nginx-based image
   - Map port `3001:80`
   - Remove `node_modules` volume mount
4. **DEPLOYMENT.md** update with nginx instructions

### Test Matrix
| Layer | What | How |
|-------|------|-----|
| Build | `docker build -f frontend/Dockerfile frontend/` | manual |
| Integration | `docker compose up` → curl localhost:3001 | manual |
| E2E | All frontend pages load correctly | manual |

### Risk: Medium
- SPA routing: `/wiki` must serve `index.html` (nginx try_files)
- Mitigation: test every route after docker up

### Rollback
- Revert docker-compose.yml to old `npm run dev` service

---

## G3: Frontend Test Framework (P3 — 2h)

### Problem
Zero frontend tests. Next.js 16 + React 19 breaking changes are only caught at build time, not by assertions.

### Deliverables
1. **Install vitest** (faster than jest for Vite-like setups):
   ```bash
   cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
   ```
2. **Config** (`frontend/vitest.config.ts`):
   - `testEnvironment: 'jsdom'`
   - `setupFiles: ['./vitest.setup.ts']`
   - Alias `@/` → `./`
3. **Setup** (`frontend/vitest.setup.ts`):
   - Import `@testing-library/jest-dom`
   - Mock `window.matchMedia`, `IntersectionObserver`
4. **Sample tests**:
   - `tests/lib/i18n.test.ts` — verify `t()` returns correct strings
   - `tests/components/NeoMetric.test.tsx` — renders label + value
   - `tests/hooks/useTrades.test.ts` — mock fetch, verify state updates
5. **CI** update: add `cd frontend && npx vitest run` to `frontend-build` job

### Test Matrix
| Layer | What | How |
|-------|------|-----|
| Unit | i18n, utility functions | vitest |
| Component | NeoCard, NeoMetric, NeoButton | @testing-library/react |
| Hook | useTrades, useSocketIO | @testing-library/react + mock server |

### Risk: Low
- New code, no existing tests to break
- Mitigation: start with 3 simple tests, expand later

### Rollback
- Remove vitest config + test files, no production impact

---

## G4: DB-Dependent Tests in CI (P2 — 1h)

### Problem
`test_backend_api.py` and `test_ml_integration.py` fail without a real PostgreSQL. CI already has a Postgres service, but these tests don't connect properly or need specific schema/data.

### Root Cause Analysis
- `test_ml_integration.py` tries `psycopg2.connect(**self.pg_config)` with host `"postgres"` which resolves only inside Docker network, not in GitHub Actions
- `test_backend_api.py` imports `TradesService` which requires `TRADING_DB_URL`

### Deliverables
1. **Fix `test_ml_integration.py`**:
   - Mock `TradeLogger` initialization or use SQLite fallback
   - OR skip if `TRADING_DB_URL` not available: `@pytest.mark.skipif(not os.environ.get("TRADING_DB_URL"))`
2. **Fix `test_backend_api.py`**:
   - It already uses `AsyncClient` with mocked services; verify it doesn't need real DB
   - Check if `TradesService()` instantiation at import time causes the error
3. **CI** update:
   - Ensure `TRADING_DB_URL` env var is set to the service URL
   - Add DB migrations before tests if needed

### Test Matrix
| Layer | What | How |
|-------|------|-----|
| CI | All 125 tests pass in GitHub Actions | `pytest tests/` |

### Risk: Low
- Only test fixes, no production code changes
- Mitigation: run locally with same env vars before pushing

### Rollback
- Skip problematic tests with `@pytest.mark.skipif`

---

## G5: Push Commits to Remote (P1 — 5min)

### Problem
`main` is 8 commits ahead of `origin/main`. All work is local.

### Deliverables
1. `git push origin main`

### Risk: None
- All tests pass locally, no force push needed

---

## Dependency Graph

```
G5 (push) ───────────────────────────────────────► [anytime]
  │
G4 (CI fix) ──depends──► G5 (push after CI green)
  │
G3 (frontend tests) ──parallel──► G2 (docker nginx)
  │
G2 (docker nginx) ──parallel──► G1 (graduation page)
  │
G1 (graduation page) ──independent──► all others
```

**Execution order**: G1, G2, G3 in parallel → G4 → G5

---

## File Ownership (Parallel Execution)

| Phase | Files | Conflicts |
|-------|-------|-----------|
| G1 | `backend/api/graduation_service.py`, `backend/api/main.py`, `frontend/app/graduation/`, `backend/api/aggregator.py` | main.py (adds route) |
| G2 | `frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.yml`, `DEPLOYMENT.md` | docker-compose.yml |
| G3 | `frontend/vitest.config.ts`, `frontend/vitest.setup.ts`, `frontend/tests/`, `.github/workflows/ci.yml` | ci.yml |
| G4 | `tests/test_ml_integration.py`, `tests/test_backend_api.py`, `.github/workflows/ci.yml` | ci.yml |

**Note**: G3 and G4 both touch `ci.yml`. G4 should wait for G3 or be merged after.

---

## Success Criteria

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 1 | `/graduation` page shows real metrics from last 30 days | Manual: open page, compare with DB trades |
| 2 | `docker compose up` serves frontend via nginx | `curl localhost:3001` returns HTML, no Node process |
| 3 | Frontend tests run in CI | `npx vitest run` passes in GitHub Actions |
| 4 | All 125 tests pass in CI | `pytest tests/` green in GitHub Actions |
| 5 | Commits pushed to remote | `git log origin/main..main` is empty |

---

## Rollback Plan (Global)

If any phase breaks production:
1. `git revert <commit>` for the specific phase
2. `docker compose down && docker compose up -d` to restart
3. Frontend static files are in `dist/` — reverting doesn't affect already-built files until rebuild

---

## Decisions (User Confirmed)

1. ✅ `/graduation` always visible — show "not enough data" when < 30 days
2. ✅ Telegram alert when graduation criteria met (reuse existing TelegramNotifier)
3. ✅ Frontend tests: vitest for unit + Playwright for visual regression

## Updated Execution Order

```
G1 (graduation + telegram alert) ──► G2 (docker nginx) ──┐
                                                          ├──► G4 (CI fix) ──► G5 (push)
G3 (vitest + Playwright) ─────────────────────────────────┘
```

---

## Next Step

Execute phases in order: **G1 → G2/G3 (parallel) → G4 → G5**

Say **"execute G1"** to start Paper Trading Graduation Monitor.
