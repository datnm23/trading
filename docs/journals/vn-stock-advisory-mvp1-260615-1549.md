# VN Stock Advisory MVP-1: Major Pivot Complete

**Date**: 2026-06-15 15:49
**Severity**: Medium
**Component**: Platform architecture, data layer, analytics engines
**Status**: Resolved (production-ready, rate-limited)

## What Happened

Pivoted entire platform from crypto trading bot to VN Stock Advisory (advisory-only, VN30 universe, MVP-1 scope). Executed 7-phase plan end-to-end: spike + cleanup → data adapters → screener → valuation → FastAPI → Next.js frontend → backtesting. Delivered 274 passing tests, 8 commits, zero test failures.

Key discovery forced architecture revision mid-flight: **vnstock library 3.5.1 finance endpoints are completely broken**. The deprecated `Vnstock()` class was disabled 31/08/2025. Upgraded to 4.0.4 and restructured all finance calls to use `vnstock.api.*` modules. This forced a cascading refactor across data layer and all analytical engines.

## The Brutal Truth

This is the right platform—VN equities advisory hits market opportunity far better than crypto trading bots—but the vnstock API fragility is **the dominant architectural constraint** going forward. Rate limit = 20 requests/minute (guest key) is not a scalability problem; it's a **correctness problem**. Screeners and backtests can't run raw—they must hit cache layers or throttle/backoff gracefully. Every missing cache miss costs 3 seconds of backoff. This isn't a performance complaint; it's a design requirement that leaked into three separate modules.

The other gut-punch: **bank vs non-bank financial statements use completely different item_id schemas.** A PE ratio calculation that works for Vietcombank (CTG) silently produces garbage for Vingroup (VIC). We branched on `is_bank` in the valuation engine, but this fragility will surface in edge cases. Future analysts will curse this.

Deleted crypto execution layer entirely. That infrastructure investment is now sunk. The rationalization: advisory-only pivot means no live execution needed. But losing that capability feels like stepping backward, even if strategically correct.

## Technical Details

**vnstock 4.0.4 API changes:**
- Old: `from vnstock import Vnstock; quote = Vnstock().quote()`
- New: `from vnstock.api import stock; price = stock.get_quote()`
- Finance endpoints: `stock.company_overview()`, `stock.income_statement()`, `stock.ratio()` (not `Vnstock().ca()`)
- Rate limit: 20 req/min guest (60 req/min with free key). No header backoff signal—detect via `429 Too Many Requests` and apply exponential backoff (2s → 4s → 8s)

**Bank/non-bank schema split:**
- Bank F-score uses different item_id keys than non-bank (e.g., gross_profit missing for banks)
- Valuation engine branches on `FinanceType.is_bank` before F-score + Altman Z′ calculation
- Piotroski F normalized within each cohort (can't compare raw scores cross-bank-type)

**Test coverage:** 274 passed / 7 skipped / 0 failed
- P1 (data layer): 7 fixes applied (OHLCV cache range-truncation, rate-limit detection)
- P2 (screener): 8.5/10 code review; self-inclusion in median fixed
- P3 (valuation): 8/10 code review; bank F-score branching verified
- Pre-existing bug fixed: `WikiSignalValidator.__init__` ignored `min_alignment` param (hardcoded 0.15 instead of respecting arg)

**Files changed:**
- Removed: `src/trading/crypto_*`, bot execution dependencies
- Added: `src/data/vn/`, `src/analytics/valuation/`, `src/api/advisory/`, `frontend/pages/screener`, `frontend/pages/stock`
- Modified: config system (advisory-mode), data cache (dual parquet+SQLite/PostgreSQL), test suite

## What We Tried

1. **Keep vnstock 3.5.1** → Endpoints 404'd in P0 spike. No fallback. Forced upgrade.
2. **Stateless rate-limit handling** → Thrashing on backoff cascades. Switched to exponential backoff + cache-first strategy.
3. **Unified bank/non-bank F-score** → Produced nonsensical rankings (banks ranked below non-banks on incomparable metrics). Branched on `is_bank` flag.
4. **Python kebab-case file naming in P6 backtest** → Not importable. Broke module loading. Renamed to snake_case + standard imports.

## Root Cause Analysis

**Why vnstock broke us:** The library is maintained by retail investors, not professionals. Version 3.5.1 finance endpoints relied on a backend API contract that changed. The maintainer responded by releasing v4 with a new module structure (`vnstock.api.*`), but deprecation was silent. We hit the wall during spike work, not during initial planning. This is not a mistake—we couldn't have known pre-flight—but it **reflects fragile upstream dependency choice**. Alternative (Fireant.vn, TCBS API) would have had similar risks. Lesson: test upstream API contracts during spike, hard-fail if broken.

**Why bank/non-bank schema matters:** Vietnam's financial regulation treats banks differently (capital requirements, profitability metrics). The vnstock schema reflects this, but the library doesn't expose it clearly. We discovered it via "why are all banks ranked below non-banks on F-score?" debugging. The fix (branch on `is_bank`) works, but **future analytical features will need the same branching**. This is not a one-time fix; it's an architectural pattern.

**Why P6 broke:** Subagent created kebab-case files (`screener-backtest.py`) and tried to load via importlib hack instead of standard Python imports. Works locally, fails in CI. Caught by test run; fixed immediately.

## Lessons Learned

1. **Spike upstream API contracts aggressively.** Don't assume npm/pip versions are stable. Test live endpoints before committing to a dependency.
2. **Cache-first + throttle-on-miss.** A 20 req/min external API is not a bottleneck if you cache aggressively. Build cache layers before analytics layers.
3. **Document schema splits explicitly.** Bank/non-bank is not a "quirk"—it's a structural feature. Document it in the data model, not as a comment in valuation.py.
4. **File naming conventions matter for import systems.** Python imports are sensitive to naming. Enforce snake_case via linting, not human review.
5. **Code review gates catch real bugs.** Every analytical engine passed review and had findings. The review-fix cycle is not overhead—it's essential quality control.

## Next Steps

1. **Production rate-limit handling:** Implement circuit-breaker + queue-retry (current backoff is naive). Feed live VN30 screener at 20 req/min with caching. Target: <100ms per request (cache hit) + graceful degradation on miss.
2. **Frontend build verification:** Next.js binary missing in test env. Verify offline build before release.
3. **Clean up dead code:** `data/feed.py`, crypto backtest/ML modules still in codebase. Deferred but must be removed before production merge.
4. **Document vnstock 4.x migration:** Create runbook for future API updates. Include: endpoint mapping, rate-limit detection, bank/non-bank schema.
5. **Expand bank/non-bank tests:** Add specific test cases for banks (CTG, VCB) and non-banks (VIC, HPG) to prevent regression.

**Owner:** Data layer owner (vnstock contracts) + DevOps (rate-limit policy).
**Timeline:** Rate-limit handling by sprint-end. Dead code cleanup before merge. Documentation before external handoff.

---

**Files:**
- Data adapters: `src/data/vn/market_data.py`, `src/data/vn/finance_data.py`
- Screener: `src/analytics/screener/ranker.py`
- Valuation: `src/analytics/valuation/dcf.py`, `src/analytics/valuation/comparative.py`, `src/analytics/valuation/piotroski_score.py`
- API: `src/api/advisory/routes.py`
- Frontend: `frontend/pages/screener.tsx`, `frontend/pages/stock.tsx`
- Tests: 274 passed
