"""Tests for Monthly Breakout strategy."""

import numpy as np
import pandas as pd

from strategies.base import StrategyContext
from strategies.rule_based.monthly_breakout import MonthlyBreakoutStrategy


def make_history_from_close(close: list, offset: float = 5) -> pd.DataFrame:
    """Build OHLCV from a close-price series."""
    close = np.array(close, dtype=float)
    n = len(close)
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    high = close + offset + np.abs(np.random.randn(n)) * 2
    low = close - offset - np.abs(np.random.randn(n)) * 2
    low = np.maximum(low, close * 0.9)
    return pd.DataFrame(
        {
            "open": close - np.random.randn(n) * 1,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.randint(1000, 10000, n),
        },
        index=dates,
    )


def make_context(history: pd.DataFrame, symbol: str = "BTC/USDT") -> StrategyContext:
    bar = history.iloc[-1]
    return StrategyContext(
        symbol=symbol,
        bar=bar,
        history=history,
        account={"balance": 10000},
        positions=[],
    )


class TestMonthlyBreakout:
    def test_breakout_up_generates_buy(self):
        # Price breaks above previous N-day high
        base = [100] * 100
        breakout = base + [105]  # close above the 90-day window high
        hist = make_history_from_close(breakout, offset=3)
        strat = MonthlyBreakoutStrategy(params={"lookback_months": 3})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "buy"
            assert sig.strength == 0.9
            assert sig.meta.get("breakout") == "up"
            assert "highest" in sig.meta
            assert "atr" in sig.meta

    def test_breakdown_generates_sell(self):
        base = [100] * 100
        breakdown = base + [95]  # close below the 90-day window low
        hist = make_history_from_close(breakdown, offset=3)
        strat = MonthlyBreakoutStrategy(params={"lookback_months": 3})
        strat.warmup(hist)
        strat.in_position = True
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "sell"
            assert sig.strength == 0.9
            assert sig.meta.get("breakout") == "down"

    def test_approaching_high_weak_buy(self):
        # Price within 2% of previous high but not yet broken
        base = [100] * 100
        close = base + [100.5]  # 0.5% below high
        hist = make_history_from_close(close, offset=2)
        strat = MonthlyBreakoutStrategy(params={"lookback_months": 3})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "buy"
            assert 0 < sig.strength <= 0.3
            assert sig.meta.get("reason") == "approaching_high"

    def test_approaching_low_weak_sell(self):
        base = [100] * 100
        close = base + [99.5]  # 0.5% above low
        hist = make_history_from_close(close, offset=2)
        strat = MonthlyBreakoutStrategy(params={"lookback_months": 3})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "sell"
            assert 0 < sig.strength <= 0.3
            assert sig.meta.get("reason") == "approaching_low"

    def test_not_warm_returns_none(self):
        strat = MonthlyBreakoutStrategy()
        hist = make_history_from_close([100, 101])
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        assert sig is None

    def test_no_signal_when_far_from_levels(self):
        # Price in the middle of the range
        close = [100] * 50 + [102] * 50
        hist = make_history_from_close(close, offset=5)
        strat = MonthlyBreakoutStrategy(params={"lookback_months": 1})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # In the middle of range, no signal
        assert sig is None

    def test_lookback_months_param(self):
        strat1 = MonthlyBreakoutStrategy(params={"lookback_months": 1})
        strat3 = MonthlyBreakoutStrategy(params={"lookback_months": 3})
        assert strat1.lookback == 30
        assert strat3.lookback == 90

    def test_reset_clears_in_position(self):
        strat = MonthlyBreakoutStrategy()
        strat.in_position = True
        strat.is_warm = True
        strat.reset()
        assert not strat.in_position
        assert not strat.is_warm

    def test_breakout_without_position_no_sell(self):
        base = [100] * 100
        breakdown = base + [95]
        hist = make_history_from_close(breakdown, offset=3)
        strat = MonthlyBreakoutStrategy(params={"lookback_months": 3})
        strat.warmup(hist)
        strat.in_position = False
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # Breakdown but no position → no sell
        assert sig is None
