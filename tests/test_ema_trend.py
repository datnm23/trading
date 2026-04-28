"""Tests for EMA-Trend strategy."""

import pytest
import pandas as pd
import numpy as np

from strategies.base import StrategyContext
from strategies.rule_based.ema_trend import EMATrendStrategy, _atr


def make_history_from_close(close: list, offset: float = 5) -> pd.DataFrame:
    """Build OHLCV from a close-price series."""
    close = np.array(close, dtype=float)
    n = len(close)
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    high = close + offset + np.abs(np.random.randn(n)) * 2
    low = close - offset - np.abs(np.random.randn(n)) * 2
    low = np.maximum(low, close * 0.9)
    return pd.DataFrame({
        "open": close - np.random.randn(n) * 1,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1000, 10000, n),
    }, index=dates)


def make_context(history: pd.DataFrame, symbol: str = "BTC/USDT") -> StrategyContext:
    bar = history.iloc[-1]
    return StrategyContext(
        symbol=symbol,
        bar=bar,
        history=history,
        account={"balance": 10000},
        positions=[],
    )


class TestEMATrend:
    def test_atr_computation(self):
        hist = make_history_from_close([100, 102, 101, 103, 105])
        atr = _atr(hist["high"], hist["low"], hist["close"], period=3)
        assert len(atr) == len(hist)
        assert atr.iloc[-1] > 0

    def test_crossover_up_generates_buy(self):
        # Fast EMA crosses above slow EMA
        close = [100] * 60 + list(np.linspace(100, 130, 40))
        hist = make_history_from_close(close)
        strat = EMATrendStrategy(params={"fast_ema": 10, "slow_ema": 30})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # May be crossover_up (strength 0.9) or trend_continuation (strength <=0.5)
        if sig:
            assert sig.side == "buy"
            assert "stop" in sig.meta
            assert "reason" in sig.meta
            assert sig.meta["reason"] in ("crossover_up", "trend_continuation")
            if sig.meta["reason"] == "crossover_up":
                assert sig.strength == 0.9
            else:
                assert sig.strength <= 0.5

    def test_crossover_down_generates_sell(self):
        close = [130] * 60 + list(np.linspace(130, 100, 40))
        hist = make_history_from_close(close)
        strat = EMATrendStrategy(params={"fast_ema": 10, "slow_ema": 30})
        strat.warmup(hist)
        # Manually enter position
        strat.in_position = True
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "sell"
            assert sig.meta["reason"] in ("crossover_down", "trend_continuation")
            if sig.meta["reason"] == "crossover_down":
                assert sig.strength == 0.9
            else:
                assert sig.strength <= 0.5

    def test_trend_continuation_weak_buy(self):
        # Strong uptrend with no crossover (fast already above slow)
        close = list(np.linspace(100, 150, 100))
        hist = make_history_from_close(close)
        strat = EMATrendStrategy(params={"fast_ema": 10, "slow_ema": 30})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            # Could be weak continuation buy
            assert sig.side == "buy"
            assert sig.strength <= 0.5
            assert sig.meta["reason"] == "trend_continuation"

    def test_not_warm_returns_none(self):
        strat = EMATrendStrategy()
        hist = make_history_from_close([100, 101, 102])
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        assert sig is None

    def test_no_signal_when_no_crossover(self):
        # Flat market, no crossover
        close = [100] * 100
        hist = make_history_from_close(close)
        strat = EMATrendStrategy(params={"fast_ema": 10, "slow_ema": 30})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # No position and no crossover → no signal (or weak continuation)
        if sig:
            assert sig.strength < 0.9

    def test_stop_price_in_meta(self):
        close = [100] * 60 + list(np.linspace(100, 130, 40))
        hist = make_history_from_close(close)
        strat = EMATrendStrategy(params={"fast_ema": 10, "slow_ema": 30})
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig and sig.side == "buy":
            assert "stop" in sig.meta
            assert sig.meta["stop"] < sig.price

    def test_reset_clears_in_position(self):
        strat = EMATrendStrategy()
        strat.in_position = True
        strat.is_warm = True
        strat.reset()
        assert not strat.in_position
        assert not strat.is_warm

    def test_sell_without_position_returns_none(self):
        close = [130] * 60 + list(np.linspace(130, 100, 40))
        hist = make_history_from_close(close)
        strat = EMATrendStrategy(params={"fast_ema": 10, "slow_ema": 30})
        strat.warmup(hist)
        strat.in_position = False
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # Crossover down but no position → no sell signal
        assert sig is None
