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

        # Cross up
        if prev_fast <= prev_slow and fast_ema > slow_ema and not self.in_position:
            self.in_position = True
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="buy",
                strength=0.8,
                price=context.bar["close"],
                meta={"fast_ema": fast_ema, "slow_ema": slow_ema, "atr": atr_val},
            )

        # Cross down
        if prev_fast >= prev_slow and fast_ema < slow_ema and self.in_position:
            self.in_position = False
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="sell",
                strength=0.8,
                price=context.bar["close"],
                meta={"fast_ema": fast_ema, "slow_ema": slow_ema, "atr": atr_val},
            )

        return None
