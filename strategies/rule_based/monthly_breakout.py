"""Monthly Breakout Strategy."""

from typing import Optional

import pandas as pd
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext
from strategies.rule_based.ema_trend import _atr


class MonthlyBreakoutStrategy(BaseStrategy):
    """Breakout above/below N-month high/low with ATR stop."""

    def __init__(self, params: Optional[dict] = None):
        super().__init__(name="Monthly-Breakout", params=params)
        self.lookback = self.params.get("lookback_months", 3) * 30  # approximate days
        self.atr_period = self.params.get("atr_period", 14)
        self.in_position = False

    def warmup(self, history: pd.DataFrame) -> None:
        if len(history) < self.lookback + 10:
            logger.warning("Not enough data for warmup")
            return
        self.is_warm = True

    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        if not self.is_warm:
            return None

        hist = context.history
        if len(hist) < self.lookback + 1:
            return None

        close = hist["close"]
        high = hist["high"]
        low = hist["low"]

        atr_val = _atr(high, low, close, self.atr_period).iloc[-1]

        # Monthly lookback levels (exclude current bar)
        window = hist.iloc[-self.lookback - 1:-1]
        highest = window["high"].max()
        lowest = window["low"].min()

        curr_close = close.iloc[-1]

        # Breakout up: close above previous N-day high
        if curr_close > highest and not self.in_position:
            self.in_position = True
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="buy",
                strength=0.9,
                price=curr_close,
                meta={"highest": highest, "lowest": lowest, "atr": atr_val, "breakout": "up"},
            )

        # Breakdown — close long when close below previous N-day low
        if curr_close < lowest and self.in_position:
            self.in_position = False
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="sell",
                strength=0.9,
                price=curr_close,
                meta={"highest": highest, "lowest": lowest, "atr": atr_val, "breakout": "down"},
            )

        return None
