"""Base strategy interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass
class Signal:
    """Trading signal produced by a strategy."""
    timestamp: pd.Timestamp
    symbol: str
    side: str          # "buy" | "sell" | "close"
    strength: float    # 0.0 - 1.0
    price: Optional[float] = None
    meta: Optional[dict] = None


@dataclass
class StrategyContext:
    """Context passed to strategy on each bar."""
    symbol: str
    bar: pd.Series
    history: pd.DataFrame
    account: dict
    positions: list


class BaseStrategy(ABC):
    """Abstract base class for all strategies."""

    def __init__(self, name: str, params: Optional[dict] = None):
        self.name = name
        self.params = params or {}
        self.is_warm = False

    @abstractmethod
    def warmup(self, history: pd.DataFrame) -> None:
        """Warm up indicators with historical data."""
        pass

    @abstractmethod
    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        """Process new bar and optionally return a signal."""
        pass

    def on_order_fill(self, order: dict) -> None:
        """Callback when an order is filled. Override if needed."""
        pass

    def reset(self) -> None:
        """Reset internal state."""
        self.is_warm = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
