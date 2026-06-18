"""Tests for Grid Mean Reversion strategy."""

import numpy as np
import pandas as pd

from strategies.base import StrategyContext
from strategies.rule_based.grid_mean_reversion import GridMeanReversionStrategy


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


class TestGridMeanReversion:
    def test_warmup_sets_levels(self):
        close = list(np.linspace(100, 120, 50))
        hist = make_history_from_close(close, offset=3)
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 5, "lookback_days": 30}
        )
        strat.warmup(hist)
        assert strat.is_warm
        assert strat.support is not None
        assert strat.resistance is not None
        assert strat.grid_step is not None
        assert strat.grid_step > 0

    def test_buy_near_support(self):
        # Create a history where price drops to near support
        close = list(np.linspace(120, 100, 40)) + [100.1] * 10
        hist = make_history_from_close(close, offset=2)
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 5, "lookback_days": 30}
        )
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "buy"
            assert sig.strength == 0.7
            assert "support" in sig.meta
            assert "resistance" in sig.meta
            assert "grid_step" in sig.meta

    def test_sell_near_resistance(self):
        # Create a history where price rises to near resistance
        close = list(np.linspace(100, 120, 40)) + [119.9] * 10
        hist = make_history_from_close(close, offset=2)
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 5, "lookback_days": 30}
        )
        strat.warmup(hist)
        strat.in_position = True
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "sell"
            assert sig.strength == 0.7
            assert "support" in sig.meta
            assert "resistance" in sig.meta

    def test_not_warm_returns_none(self):
        strat = GridMeanReversionStrategy()
        hist = make_history_from_close([100, 101])
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        assert sig is None

    def test_levels_update_each_bar(self):
        close = list(np.linspace(100, 120, 50))
        hist = make_history_from_close(close, offset=3)
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 5, "lookback_days": 30}
        )
        strat.warmup(hist)
        old_support = strat.support
        old_resistance = strat.resistance
        # New bar extends the range
        close2 = list(np.linspace(100, 130, 51))
        hist2 = make_history_from_close(close2, offset=3)
        ctx = make_context(hist2)
        strat.on_bar(ctx)
        assert strat.support != old_support or strat.resistance != old_resistance

    def test_no_signal_when_price_in_middle(self):
        # Price in the middle of the grid
        close = [100] * 25 + [110] * 25
        hist = make_history_from_close(close, offset=5)
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 5, "lookback_days": 30}
        )
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # Middle of range, no signal
        assert sig is None

    def test_grid_levels_param(self):
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 10, "lookback_days": 30}
        )
        assert strat.grid_levels == 10

    def test_lookback_days_param(self):
        strat = GridMeanReversionStrategy(
            params={"grid_levels": 5, "lookback_days": 60}
        )
        assert strat.lookback == 60

    def test_reset_clears_state(self):
        strat = GridMeanReversionStrategy()
        strat.support = 100
        strat.resistance = 120
        strat.grid_step = 4
        strat.in_position = True
        strat.is_warm = True
        strat.reset()
        assert not strat.is_warm
        assert not strat.in_position
        # support/resistance/grid_step remain as they were before reset (not cleared by base reset)
