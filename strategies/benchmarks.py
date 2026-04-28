"""Benchmark strategies for comparison."""

import pandas as pd

from strategies.base import BaseStrategy, Signal, StrategyContext


class BuyHoldStrategy(BaseStrategy):
    """Buy at first bar and hold until end of period.

    Used as a benchmark to compare against active trading strategies.
    """

    def __init__(self, params: dict | None = None):
        super().__init__(name="BuyHold", params=params)
        self.has_bought = False

    def warmup(self, history: pd.DataFrame) -> None:
        self.is_warm = True

    def reset(self) -> None:
        super().reset()
        self.has_bought = False

    def on_bar(self, context: StrategyContext) -> Signal | None:
        if not self.is_warm:
            return None
        if not self.has_bought:
            self.has_bought = True
            return Signal(
                timestamp=context.bar.name,
                symbol=context.symbol,
                side="buy",
                strength=1.0,
                price=context.bar["close"],
                meta={"reason": "buy_and_hold_entry"},
            )
        return None
