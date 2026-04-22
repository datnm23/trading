# ML-XGBoost Heavy Modification Plan

## Context

ML-XGBoost v2 (threshold=0.75 + trend filter + cost-aware weights + 63 features) achieved:
- **Net Return: -5.2%** (still negative)
- **Gross Return: -1.5%** (signals lack alpha)
- **Total Cost: $3,732** (down from $17,179 in v1)
- **Trades: 63** (down from 294 in v1)

The trend filter and threshold raised to 0.75 dramatically reduced costs, but the **model still lacks predictive edge**. The feature importance analysis reveals `ema_5` (4.79%) and `close_lag_1` (2.32%) dominate splits — short-term noise drowning out macro signals.

## Execution Plan (Sequential, One Variable at a Time)

---

### Phase 1: Quick Win — Threshold Tuning (Est. 10 min)

**Hypothesis:** High-confidence predictions (>0.80) may have genuine alpha.

**Change:** `threshold = 0.80` (from 0.75)

**Baseline for comparison:** ML-XGBoost v2 (threshold=0.75)
- Net Return: -5.2%
- Gross Return: -1.5%
- Trades: 63
- Cost: $3,732

**Expected outcomes:**

| Scenario | Gross Return | Trades | Interpretation | Next Action |
|----------|-------------|--------|----------------|-------------|
| **A: Alpha confirmed** | > 0% | 25-40 | High-confidence signals have real edge | Fine-tune threshold, test 0.85 |
| **B: No-trade bot** | ~0% | < 20 | Model lacks alpha, just trading less | Proceed to Phase 2 |
| **C: Weak alpha** | -3% to 0% | 30-50 | Slight improvement but not enough | Proceed to Phase 2 |

---

### Phase 2: Feature Surgery (Est. 30 min)

**Hypothesis:** Short-term features dominate splits, drowning out long-term signals.

**Change:** Whitelist features — drop all short-term noise, keep only macro/trend features.

**Feature groups:**

| Category | Keep | Drop |
|----------|------|------|
| Moving Averages | `ema_50/100/200`, `sma_50/100/200` | `ema_5/10`, `sma_5/10` |
| Returns | `returns_20/50/100d` | `returns_1d`, `returns_lag_1/2/3/5` |
| Volatility | `volatility_20/50/100d` | `volatility_5/10d` |
| Trend | `ema_slope_20/50` | `close_lag_1/2/3/5` |
| Momentum | `macd`, `macd_signal`, `macd_hist`, `rsi_14` | — |
| Positioning | `close_to_ema_50/100/200`, `close_to_sma_50/100/200` | `close_to_ema_5/10`, `close_to_sma_5/10/20` |
| Volume | `obv_ema` | `volume_change`, `volume_ratio`, `volume_sma_10` |
| Price Action | `bb_position`, `atr_ratio` | `body_size`, `upper_shadow`, `lower_shadow` |

**Feature count:** 63 → ~28

**Target remains:** `direction_5d` (unchanged for this phase)

**Expected outcome:** Model forced to use long-term features. If Gross Return still negative, move to Phase 3.

---

### Phase 3: Extend Target Horizon (Est. 45 min)

**Hypothesis:** 5d horizon (20 hours) is too short for macro features to matter.

**Change:** `target_return_5d` → `target_return_20d` (3.3 days)

**Why 20d?**
- 5d = 20 hours: micro-noise dominates
- 20d = 80 hours ≈ 3.3 days: swing moves, enough for 50d/100d EMAs to have predictive power
- 30d = 5 days: trend moves, but too few samples per quarter for walk-forward

**Feature set:** Same as Phase 2 whitelist (~28 features)

**Expected outcome:** If macro features truly have alpha, Gross Return should improve significantly with longer horizon.

---

### Phase 4: Cost-Aware Custom Loss (Conditional, Est. 60 min)

**Trigger:** Only if Gross Return > 0 but Net Return still negative after Phase 3.

**Change:** Custom XGBoost objective function that penalizes predictions where expected profit < transaction costs.

```python
def cost_aware_objective(y_true, y_pred):
    # Base: binary logloss
    # Add penalty: if |proba - 0.5| is small → high cost of being wrong
    # Scale penalty by (commission + slippage) / typical_move
```

---

## Execution Order

```
Phase 1 (threshold 0.80)
    |
    +-- If Gross > 0% → Done, tune further
    +-- If Gross <= 0% → Phase 2
        |
        Phase 2 (feature whitelist)
            |
            +-- If Gross > 0% → Done
            +-- If Gross <= 0% → Phase 3
                |
                Phase 3 (target 20d)
                    |
                    +-- If Gross > 0% → Done
                    +-- If Gross <= 0% → Phase 4 or HALT
```

## Conclusion

**DECISION: HALT ML-XGBoost. Pivot to RegimeEnsemble as core strategy.**

After 3 phases of heavy modification, **ML-XGBoost fails to achieve positive gross return** on BTC/USDT 4h walk-forward data:

| Configuration | Gross Return | Net Return | Trades | Assessment |
|---------------|-------------|-----------|--------|------------|
| v1 (baseline, 63 features) | -2.9% | -20.1% | 294 | Overtrading, cost destroyed returns |
| v2 (+ threshold 0.75 + trend filter) | -1.5% | -5.2% | 63 | Cost reduced 78%, still no alpha |
| Phase 1 (threshold 0.80) | **-0.8%** | -4.0% | 55 | Best result, but still no alpha |
| Phase 2 (feature whitelist 28) | -5.4% | -8.7% | 56 | Worse than Phase 1; short-term features had weak predictive value |
| Phase 3 (whitelist + target 20d) | -2.1% | -5.8% | 62 | Longer horizon didn't rescue the model |
| **RegimeEnsemble (wiki+psych)** | **+58.0%** | **+53.7%** | **33** | **Clear alpha, robust across periods** |
| **BuyHold** | **+19.0%** | **+18.4%** | **9** | **Simple benchmark** |

**Key insight:** The model's predictive accuracy (~52-58%) is insufficient to overcome transaction costs. No configuration of threshold, feature selection, or target horizon has produced genuine alpha. RegimeEnsemble, built on 683 Turtle Trading Wiki concepts + behavioral psychology, demonstrably outperforms.

**Next steps for RegimeEnsemble:**
1. Optimize position sizing / risk parameters per regime
2. Add ML-derived signals as a *secondary* input (not primary decision maker)
3. Deploy live with RegimeEnsemble as core, BuyHold as fallback

**Future ML experiments (low priority):**
- Option 5: Regime-specific training (bull/bear/sideways models)
- Option 3/4: Advanced architectures + on-chain/sentiment data (high effort, deferred)

## Files Modified

| File | Changes |
|------|---------|
| `scripts/run_walkforward.py` | Phase 1-3 configurations, naming |
| `ml/features/engineering.py` | `LONG_TERM_WHITELIST`, `target_return_20d`, configurable `prepare_train_data` |
| `ml/pipelines/xgboost_pipeline.py` | `feature_whitelist` and `target_horizon` support |

## Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| Gross Return | > 0% | Must be positive — proves alpha exists |
| Net Return | > 0% | After all costs |
| Total Trades | 15-50 per quarter | Not too few (no-trade bot), not too many (overtrading) |
| Avg Cost/Trade | < $80 | Current is ~$59, should stay reasonable |

## Progress Log

| Phase | Status | Date | Gross Return | Net Return | Trades | Notes |
|-------|--------|------|-------------|-----------|--------|-------|
| Baseline (v1) | Done | 2026-04-22 | -2.9% | -20.1% | 294 | Overtrading, cost killed it |
| v2 (threshold 0.75 + trend filter) | Done | 2026-04-22 | -1.5% | -5.2% | 63 | Cost reduced 78%, but still no alpha |
| Phase 1 (threshold 0.80) | Done | 2026-04-22 | -0.8% | -4.0% | 55 | Fewer trades, gross still negative |
| Phase 2 (feature whitelist) | Done | 2026-04-22 | -5.4% | -8.7% | 56 | Worse than Phase 1; short-term features had weak predictive value |
| Phase 3 (whitelist + target 20d) | Done | 2026-04-22 | -2.1% | -5.8% | 62 | Slightly better than Phase 2 but still no alpha |
| Phase 4 (custom loss) | **HALTED** | | | | | Gross still negative; custom loss cannot create alpha from none |
