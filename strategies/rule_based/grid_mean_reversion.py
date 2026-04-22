"""Grid Mean Reversion Strategy."""

from typing import Optional

import pandas as pd
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext
from strategies.rule_based.ema_trend import _atr


class GridMeanReversionStrategy(BaseStrategy):
    """Buy near support, sell near resistance in a defined grid."""

    def __init__(self, params: Optional[dict] = None):
        super().__init__(name="Grid-MeanReversion", params=params)
        self.grid_levels = self.params.get("grid_levels", 5)
        self.lookback = self.params.get("lookback_days", 30)
        self.atr_period = self.params.get("atr_period", 14)
        self.in_position = False
        self.support = None
        self.resistance = None
        self.grid_step = None

    def warmup(self, history: pd.DataFrame) -> None:
        if len(history) < self.lookback + 10:
            logger.warning("Not enough data for warmup")
            return
        self._update_levels(history)
        self.is_warm = True

    def _update_levels(self, history: pd.DataFrame):
        window = history.iloc[-self.lookback:]
        self.support = window["low"].min()
        self.resistance = window["high"].max()
        self.grid_step = (self.resistance - self.support) / self.grid_levels

    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        if not self.is_warm:
            return None

        hist = context.history
        self._update_levels(hist)

        close = hist["close"].iloc[-1]
        atr_val = _atr(hist["high"], hist["low"], hist["close"], self.atr_period).iloc[-1]

        # Buy when price is within 1 grid step above support
        if not self.in_position and close <= self.support + self.grid_step * 1.5:
            self.in_position = True
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="buy",
                strength=0.7,
                price=close,
                meta={"support": self.support, "resistance": self.resistance, "atr": atr_val, "grid_step": self.grid_step},
            )

        # Sell when price is within 1 grid step below resistance
        if self.in_position and close >= self.resistance - self.grid_step * 1.5:
            self.in_position = False
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="sell",
                strength=0.7,
                price=close,
                meta={"support": self.support, "resistance": self.resistance, "atr": atr_val, "grid_step": self.grid_step},
            )

        return None
