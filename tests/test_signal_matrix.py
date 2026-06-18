"""Offline tests for the unified signal decision matrix (P0 thresholds).

Covers `StockService._decide` (2-axis tech × value matrix) and `_display_score`.
Pure methods — only read module-level `_SIGNAL_CFG`; source is never touched.
Run: python3 -m pytest tests/test_signal_matrix.py -q   (no TRADING_DB_URL)
"""
from __future__ import annotations

from backend.api.stock_service import StockService, _SIGNAL_CFG


def _svc() -> StockService:
    # source unused by _decide/_display_score — pass a sentinel.
    return StockService(source=object())


GOOD = _SIGNAL_CFG["tech_good"] + 5    # clearly TỐT
BAD = _SIGNAL_CFG["tech_bad"] - 5      # clearly XẤU
MID = (_SIGNAL_CFG["tech_good"] + _SIGNAL_CFG["tech_bad"]) / 2


class TestDecideMatrix:
    def test_zero_upside_is_not_buy(self):
        """P0 core: tech tốt + upside ≈ 0 (reliable) must NOT be BUY."""
        assert _svc()._decide(GOOD, 0.0, reliable=True) == "HOLD"

    def test_below_buy_threshold_is_hold(self):
        # upside +5% < buy_upside (+8%) → not RẺ
        assert _svc()._decide(GOOD, 0.05, reliable=True) == "HOLD"

    def test_real_upside_with_good_tech_is_buy(self):
        assert _svc()._decide(GOOD, 0.12, reliable=True) == "BUY"

    def test_bad_tech_rich_value_is_sell(self):
        assert _svc()._decide(BAD, -0.20, reliable=True) == "SELL"

    def test_mild_downside_not_sell(self):
        # upside -10% > sell_upside (-15%) → not ĐẮT enough
        assert _svc()._decide(BAD, -0.10, reliable=True) == "HOLD"

    def test_unreliable_good_tech_is_hold(self):
        assert _svc()._decide(GOOD, None, reliable=False) == "HOLD"

    def test_unreliable_weak_tech_is_insufficient(self):
        assert _svc()._decide(MID, None, reliable=False) == "INSUFFICIENT"

    def test_reliable_but_no_upside_falls_back(self):
        # upside None despite reliable flag → treated as no-value branch
        assert _svc()._decide(GOOD, None, reliable=True) == "HOLD"


class TestDisplayScore:
    def test_tech_only_when_unreliable(self):
        assert _svc()._display_score(80.0, None, reliable=False) == 80.0

    def test_blend_when_reliable(self):
        # upside 0 → val_norm 50; blend 0.5*80 + 0.5*50 = 65
        assert _svc()._display_score(80.0, 0.0, reliable=True) == 65.0

    def test_score_clamped_0_100(self):
        s = _svc()._display_score(100.0, 1.0, reliable=True)  # huge upside clamps val_norm→100
        assert 0.0 <= s <= 100.0
