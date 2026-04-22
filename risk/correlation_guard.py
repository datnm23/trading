"""Correlation Risk Guard — Prevents over-concentration in correlated assets."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger


class CorrelationGuard:
    """Checks correlation between held positions and rejects new trades if too correlated.

    Usage:
        guard = CorrelationGuard(max_correlation=0.80, lookback=90)
        guard.update_data(symbol, df)  # feed price history
        is_safe, reason = guard.check_new_position(new_symbol, held_symbols)
        if not is_safe:
            reject_trade(reason)
    """

    def __init__(self, max_correlation: float = 0.80, lookback_days: int = 90):
        self.max_correlation = max_correlation
        self.lookback_days = lookback_days
        self.price_history: Dict[str, pd.Series] = {}
        self.correlation_matrix: Optional[pd.DataFrame] = None

    def update_data(self, symbol: str, df: pd.DataFrame, price_col: str = "close"):
        """Store price history for correlation calculation."""
        if df.empty or price_col not in df.columns:
            return
        prices = df[price_col].dropna()
        if len(prices) > self.lookback_days:
            prices = prices.iloc[-self.lookback_days:]
        self.price_history[symbol] = prices
        self._recalculate()

    def _recalculate(self):
        """Recalculate correlation matrix from stored price histories."""
        if len(self.price_history) < 2:
            self.correlation_matrix = None
            return

        # Align all series and compute returns
        df = pd.DataFrame(self.price_history)
        returns = df.pct_change().dropna()
        if returns.empty or len(returns) < 10:
            self.correlation_matrix = None
            return

        self.correlation_matrix = returns.corr()

    def check_new_position(self, new_symbol: str, held_symbols: List[str]) -> Tuple[bool, str]:
        """Check if adding new_symbol would create excessive correlation risk.

        Returns:
            (is_safe, reason)
        """
        if not held_symbols:
            return True, "No existing positions"

        if self.correlation_matrix is None or new_symbol not in self.correlation_matrix.columns:
            return True, "Insufficient correlation data"

        max_corr = 0.0
        max_sym = ""
        for held in held_symbols:
            if held not in self.correlation_matrix.columns:
                continue
            corr = self.correlation_matrix.loc[new_symbol, held]
            if abs(corr) > max_corr:
                max_corr = abs(corr)
                max_sym = held

        if max_corr >= self.max_correlation:
            return False, f"Correlation {max_corr:.2f} with {max_sym} exceeds max {self.max_correlation:.2f}"

        return True, f"Max correlation {max_corr:.2f} with {max_sym} — acceptable"

    def get_correlation(self, sym1: str, sym2: str) -> Optional[float]:
        """Get correlation between two symbols."""
        if self.correlation_matrix is None:
            return None
        if sym1 not in self.correlation_matrix.columns or sym2 not in self.correlation_matrix.columns:
            return None
        return self.correlation_matrix.loc[sym1, sym2]

    def summary(self) -> Dict[str, any]:
        """Return current correlation matrix summary."""
        return {
            "symbols_tracked": list(self.price_history.keys()),
            "matrix_shape": self.correlation_matrix.shape if self.correlation_matrix is not None else None,
            "max_correlation_threshold": self.max_correlation,
        }
