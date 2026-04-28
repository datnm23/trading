"""Monthly Breakout Strategy."""

import pandas as pd
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext
from strategies.rule_based.ema_trend import _atr


class MonthlyBreakoutStrategy(BaseStrategy):
    """Breakout above/below N-month high/low with ATR stop."""

    def __init__(self, params: dict | None = None):
        super().__init__(name="Monthly-Breakout", params=params)
        self.lookback = self.params.get("lookback_months", 3) * 30  # approximate days
        self.atr_period = self.params.get("atr_period", 14)
        self.in_position = False

    def warmup(self, history: pd.DataFrame) -> None:
        if len(history) < self.lookback + 10:
            logger.warning("Not enough data for warmup")
            return
        self.is_warm = True

    def reset(self) -> None:
        super().reset()
        self.in_position = False

    def on_bar(self, context: StrategyContext) -> Signal | None:
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
        window = hist.iloc[-self.lookback - 1 : -1]
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
                meta={
                    "highest": highest,
                    "lowest": lowest,
                    "atr": atr_val,
                    "breakout": "up",
                    "reason": "breakout",
                },
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
                meta={
                    "highest": highest,
                    "lowest": lowest,
                    "atr": atr_val,
                    "breakout": "down",
                    "reason": "breakdown",
                },
            )

        # Trend continuation — weak signal for ensemble when price is near breakout level
        if not self.in_position:
            # Price is within 2% of the high — potential breakout forming
            dist_to_high = (highest - curr_close) / highest
            if 0 < dist_to_high < 0.02:
                strength = 0.3 * (
                    1 - dist_to_high / 0.02
                )  # Scale 0→0.3 as price approaches high
                return Signal(
                    timestamp=context.bar.name,
                    symbol=context.symbol,
                    side="buy",
                    strength=strength,
                    price=curr_close,
                    meta={
                        "highest": highest,
                        "lowest": lowest,
                        "atr": atr_val,
                        "breakout": "none",
                        "reason": "approaching_high",
                    },
                )
            # Price is within 2% of the low — potential breakdown forming
            dist_to_low = (curr_close - lowest) / lowest
            if 0 < dist_to_low < 0.02:
                strength = 0.3 * (1 - dist_to_low / 0.02)
                return Signal(
                    timestamp=context.bar.name,
                    symbol=context.symbol,
                    side="sell",
                    strength=strength,
                    price=curr_close,
                    meta={
                        "highest": highest,
                        "lowest": lowest,
                        "atr": atr_val,
                        "breakout": "none",
                        "reason": "approaching_low",
                    },
                )

        return None
