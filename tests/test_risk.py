"""Tests for risk management layer."""

import pytest
from risk.manager import (
    PositionSizer,
    StopLossManager,
    DrawdownGuard,
    RiskManager,
)


class TestPositionSizer:
    def test_fixed_fractional(self):
        sizer = PositionSizer(risk_per_trade=0.01, method="fixed_fractional")
        size = sizer.size(capital=100000, entry=50000, stop=49000)
        # risk_amount = 1000, price_risk = 1000, size = 1.0
        assert size == pytest.approx(1.0, rel=1e-3)

    def test_atr_based(self):
        sizer = PositionSizer(risk_per_trade=0.01, method="atr_based")
        size = sizer.size(capital=100000, entry=50000, stop=49000, atr=500)
        # price_risk = 2 * 500 = 1000, risk_amount = 1000, size = 1.0
        assert size == pytest.approx(1.0, rel=1e-3)

    def test_atr_fallback(self):
        sizer = PositionSizer(risk_per_trade=0.01, method="atr_based")
        size = sizer.size(capital=100000, entry=50000, stop=49000, atr=None)
        # Falls back to fixed fractional
        assert size == pytest.approx(1.0, rel=1e-3)

    def test_kelly(self):
        sizer = PositionSizer(risk_per_trade=0.01, method="kelly")
        size = sizer.size(capital=100000, entry=50000, stop=49000)
        # Kelly uses fixed fraction 0.25
        assert size == pytest.approx(0.5, rel=1e-3)

    def test_zero_risk(self):
        sizer = PositionSizer()
        size = sizer.size(capital=100000, entry=50000, stop=50000)
        assert size == 0.0

    def test_turtle_n(self):
        sizer = PositionSizer(risk_per_trade=0.01, method="turtle_n")
        # N = 500 (20-day ATR), risk = $1000, stop = 2N = $1000 away
        size = sizer.size(capital=100000, entry=50000, stop=0, atr=500)
        # risk_amount = 1000, price_risk = 2 * 500 = 1000, size = 1.0
        assert size == pytest.approx(1.0, rel=1e-3)

    def test_turtle_n_fallback(self):
        sizer = PositionSizer(risk_per_trade=0.01, method="turtle_n")
        # No ATR provided → fallback to fixed fractional
        size = sizer.size(capital=100000, entry=50000, stop=49000, atr=None)
        assert size == pytest.approx(1.0, rel=1e-3)

    def test_turtle_unit_size_static(self):
        # Capital $100,000, N = $500, risk = 1%
        size = PositionSizer.turtle_unit_size(capital=100000, n_value=500, risk_pct=0.01)
        # $1,000 / $500 = 2 units
        assert size == pytest.approx(2.0, rel=1e-3)

    def test_turtle_stop_buy(self):
        stop = PositionSizer.turtle_stop(entry=50000, n_value=500, side="buy", n_multiple=2.0)
        assert stop == pytest.approx(49000)

    def test_turtle_stop_sell(self):
        stop = PositionSizer.turtle_stop(entry=50000, n_value=500, side="sell", n_multiple=2.0)
        assert stop == pytest.approx(51000)


class TestStopLossManager:
    def test_fixed_buy(self):
        stop = StopLossManager.fixed(50000, "buy", pct=0.02)
        assert stop == pytest.approx(49000)

    def test_fixed_sell(self):
        stop = StopLossManager.fixed(50000, "sell", pct=0.02)
        assert stop == pytest.approx(51000)

    def test_atr_buy(self):
        stop = StopLossManager.atr_based(50000, "buy", atr=1000, multiplier=2.0)
        assert stop == pytest.approx(48000)

    def test_atr_sell(self):
        stop = StopLossManager.atr_based(50000, "sell", atr=1000, multiplier=2.0)
        assert stop == pytest.approx(52000)


class TestDrawdownGuard:
    def test_trigger(self):
        guard = DrawdownGuard(max_drawdown_pct=0.10)
        assert guard.update(100000) is False
        assert guard.update(95000) is False
        assert guard.update(89000) is True
        assert guard.is_triggered is True

    def test_reset(self):
        guard = DrawdownGuard(max_drawdown_pct=0.10)
        guard.update(100000)
        guard.update(80000)
        assert guard.is_triggered is True
        guard.reset()
        assert guard.is_triggered is False
        assert guard.peak == 0.0

    def test_new_peak(self):
        guard = DrawdownGuard(max_drawdown_pct=0.10)
        guard.update(100000)
        guard.update(95000)
        guard.update(110000)
        assert guard.peak == 110000
        assert guard.update(100000) is False  # DD from new peak is ~9%


class TestRiskManager:
    def test_check_pass(self):
        rm = RiskManager({
            "max_risk_per_trade": 0.01,
            "max_total_exposure": 0.50,
            "max_drawdown_pct": 0.15,
        })
        status = rm.check(capital=100000, equity=100000, open_positions=[])
        assert status["halted"] is False
        assert status["exposure_ok"] is True

    def test_exposure_fail(self):
        rm = RiskManager({
            "max_risk_per_trade": 0.01,
            "max_total_exposure": 0.05,
            "max_drawdown_pct": 0.15,
        })
        positions = [{"notional": 10000}]
        status = rm.check(capital=100000, equity=100000, open_positions=positions)
        assert status["exposure_ok"] is False
        assert status["total_exposure"] == pytest.approx(0.10)

    def test_drawdown_halt(self):
        rm = RiskManager({
            "max_risk_per_trade": 0.01,
            "max_total_exposure": 0.50,
            "max_drawdown_pct": 0.10,
        })
        rm.guard.update(100000)
        rm.guard.update(90000)  # 10% drawdown
        status = rm.check(capital=100000, equity=85000, open_positions=[])
        assert status["halted"] is True
