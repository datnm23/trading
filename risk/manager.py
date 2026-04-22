"""Risk management layer: position sizing, stop-loss, drawdown guard."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class RiskProfile:
    """Risk parameters for a single trade."""
    symbol: str
    entry_price: float
    stop_price: float
    target_price: Optional[float] = None
    risk_amount: float = 0.0        # absolute $ risk
    position_size: float = 0.0      # quantity / notional
    leverage: float = 1.0


class PositionSizer:
    """Calculate position size based on risk rules.

    Methods:
        - fixed_fractional: risk amount / (entry - stop)
        - atr_based: risk amount / (2 * ATR)
        - kelly: simplified Kelly fraction
        - turtle_n: Turtle Trading N-value sizing (20-day ATR)
    """

    def __init__(self, risk_per_trade: float = 0.01, method: str = "fixed_fractional"):
        self.risk_per_trade = risk_per_trade
        self.method = method

    def size(self, capital: float, entry: float, stop: float, atr: Optional[float] = None) -> float:
        """Return position size (number of units).

        Args:
            capital: Total account equity
            entry: Entry price
            stop: Stop-loss price
            atr: ATR value (used for atr_based and turtle_n methods)
        """
        risk_amount = capital * self.risk_per_trade

        if self.method == "turtle_n":
            # Turtle N = 20-day ATR
            # Unit size = (Account * risk%) / N
            # Stop is placed at entry - 2N
            if atr is not None and atr > 0:
                n_value = atr  # assume caller passes 20-day ATR as N
                price_risk = 2.0 * n_value  # Turtle system uses 2N stop
            else:
                # Fallback to fixed fractional
                price_risk = abs(entry - stop)
                if price_risk <= 0:
                    return 0.0
            return risk_amount / price_risk

        elif self.method == "atr_based":
            if atr is not None and atr > 0:
                price_risk = atr * 2.0  # 2x ATR stop
            else:
                # Fallback to fixed fractional when ATR not available
                price_risk = abs(entry - stop)
                if price_risk <= 0:
                    return 0.0

        elif self.method == "fixed_fractional":
            price_risk = abs(entry - stop)
            if price_risk <= 0:
                return 0.0

        elif self.method == "kelly":
            # Simplified Kelly: requires winrate and payoff — placeholder
            kelly_fraction = 0.25
            return (capital * kelly_fraction) / entry
        else:
            price_risk = abs(entry - stop)
            if price_risk <= 0:
                return 0.0

        return risk_amount / price_risk

    @staticmethod
    def turtle_unit_size(capital: float, n_value: float, risk_pct: float = 0.01) -> float:
        """Pure Turtle N-value unit size calculation.

        Formula: unit = (capital * risk_pct) / N
        Where N is the 20-day Average True Range.

        Example:
            Capital = $100,000, N = $500, risk = 1%
            Unit = $1,000 / $500 = 2 units
        """
        if n_value <= 0:
            return 0.0
        risk_amount = capital * risk_pct
        return risk_amount / n_value

    @staticmethod
    def turtle_stop(entry: float, n_value: float, side: str = "buy", n_multiple: float = 2.0) -> float:
        """Calculate Turtle-style stop loss at N-multiple below/above entry.

        Args:
            entry: Entry price
            n_value: N (20-day ATR)
            side: 'buy' or 'sell'
            n_multiple: Stop distance in N units (default 2.0)
        """
        if side == "buy":
            return entry - n_value * n_multiple
        return entry + n_value * n_multiple


class StopLossManager:
    """Track and update stop-loss levels."""

    @staticmethod
    def fixed(price: float, side: str, pct: float = 0.02) -> float:
        """Fixed percentage stop."""
        if side == "buy":
            return price * (1 - pct)
        return price * (1 + pct)

    @staticmethod
    def atr_based(price: float, side: str, atr: float, multiplier: float = 2.0) -> float:
        """ATR-based stop."""
        if side == "buy":
            return price - atr * multiplier
        return price + atr * multiplier


class DrawdownGuard:
    """Circuit breaker when drawdown exceeds threshold."""

    def __init__(self, max_drawdown_pct: float = 0.15):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak = 0.0
        self.is_triggered = False

    def update(self, equity: float) -> bool:
        """Return True if trading should halt."""
        if equity > self.peak:
            self.peak = equity
        if self.peak <= 0:
            return False
        drawdown = (self.peak - equity) / self.peak
        if drawdown >= self.max_drawdown_pct:
            self.is_triggered = True
            return True
        return False

    def reset(self):
        self.peak = 0.0
        self.is_triggered = False


class RiskManager:
    """Orchestrates all risk components."""

    def __init__(self, config: dict):
        self.sizer = PositionSizer(
            risk_per_trade=config.get("max_risk_per_trade", 0.01),
            method=config.get("position_sizing", "fixed_fractional")
        )
        self.stop = StopLossManager()
        self.guard = DrawdownGuard(
            max_drawdown_pct=config.get("max_drawdown_pct", 0.15)
        )
        self.max_exposure = config.get("max_total_exposure", 0.10)

    def check(self, capital: float, equity: float, open_positions: list) -> dict:
        """Return risk status and any halt signals."""
        halted = self.guard.update(equity)
        total_exposure = sum(p.get("notional", 0) for p in open_positions) / capital if capital > 0 else 0
        exposure_ok = total_exposure < self.max_exposure
        return {
            "halted": halted,
            "exposure_ok": exposure_ok,
            "total_exposure": total_exposure,
            "drawdown": self.guard.peak and (self.guard.peak - equity) / self.guard.peak,
        }
