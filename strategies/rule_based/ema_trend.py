"""EMA Trend Following Strategy."""

from typing import Optional

import pandas as pd
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Average True Range using pure pandas."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


class EMATrendStrategy(BaseStrategy):
    """Simple EMA crossover with ATR stop."""

    def __init__(self, params: Optional[dict] = None):
        super().__init__(name="EMA-Trend", params=params)
        self.fast = self.params.get("fast_ema", 20)
        self.slow = self.params.get("slow_ema", 50)
        self.atr_period = self.params.get("atr_period", 14)
        self.in_position = False

    def warmup(self, history: pd.DataFrame) -> None:
        if len(history) < self.slow + 10:
            logger.warning("Not enough data for warmup")
            return
        self.is_warm = True

    def reset(self) -> None:
        super().reset()
        self.in_position = False

    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        if not self.is_warm:
            return None

        hist = context.history
        if len(hist) < self.slow + 1:
            return None

        close = hist["close"]
        fast_ema = close.ewm(span=self.fast).mean().iloc[-1]
        slow_ema = close.ewm(span=self.slow).mean().iloc[-1]
        atr_val = _atr(hist["high"], hist["low"], close, self.atr_period).iloc[-1]

        prev_fast = close.ewm(span=self.fast).mean().iloc[-2]
        prev_slow = close.ewm(span=self.slow).mean().iloc[-2]

        current_price = context.bar["close"]

        # Cross up → strong buy signal
        if prev_fast <= prev_slow and fast_ema > slow_ema and not self.in_position:
            self.in_position = True
            stop_price = current_price - atr_val * 2
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="buy",
                strength=0.9,
                price=current_price,
                meta={"fast_ema": fast_ema, "slow_ema": slow_ema, "atr": atr_val, "reason": "crossover_up", "stop": stop_price, "stop_price": stop_price},
            )

        # Cross down → strong sell signal (exit)
        if prev_fast >= prev_slow and fast_ema < slow_ema and self.in_position:
            self.in_position = False
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="sell",
                strength=0.9,
                price=current_price,
                meta={"fast_ema": fast_ema, "slow_ema": slow_ema, "atr": atr_val, "reason": "crossover_down"},
            )

        # Trend continuation → weaker signal for aggregation
        if fast_ema > slow_ema and not self.in_position:
            # Uptrend but no crossover — produce a weak buy signal for ensemble
            gap_pct = (fast_ema - slow_ema) / slow_ema * 100
            strength = min(0.5, gap_pct / 10)  # Scale strength by gap
            stop_price = current_price - atr_val * 2
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="buy",
                strength=strength,
                price=current_price,
                meta={"fast_ema": fast_ema, "slow_ema": slow_ema, "atr": atr_val, "reason": "trend_continuation", "stop": stop_price, "stop_price": stop_price},
            )

        if fast_ema < slow_ema and self.in_position:
            # Downtrend continuation — produce weak sell signal
            gap_pct = (slow_ema - fast_ema) / slow_ema * 100
            strength = min(0.5, gap_pct / 10)
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="sell",
                strength=strength,
                price=current_price,
                meta={"fast_ema": fast_ema, "slow_ema": slow_ema, "atr": atr_val, "reason": "trend_continuation"},
            )

        return None
