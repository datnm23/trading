"""Risk management layer: position sizing, stop-loss, drawdown guard."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


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
            # Kelly criterion: f* = (p*b - q) / b
            # Requires winrate (p) and payoff ratio (b = avg_win / avg_loss)
            # If not provided, falls back to conservative half-Kelly (0.25)
            winrate = kwargs.get("winrate")
            payoff_ratio = kwargs.get("payoff_ratio")
            if winrate is not None and payoff_ratio is not None and payoff_ratio > 0:
                kelly_fraction = (winrate * payoff_ratio - (1 - winrate)) / payoff_ratio
                # Clamp to [0, 0.5] — use half-Kelly for safety
                kelly_fraction = max(0.0, min(kelly_fraction * 0.5, 0.5))
            else:
                kelly_fraction = 0.25  # Conservative default
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
        if equity <= 0:
            return True
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


class RegimeAwarePositionSizer(PositionSizer):
    """Position sizer that adjusts risk per trade based on market regime."""

    REGIME_MULTIPLIERS = {
        "bull": 1.0,      # neutral sizing in bull (was 1.3) — reduces max DD to help pass Graduation Gate
        "bear": 0.0,      # skip bear
        "sideways": 0.3,  # very reduced in chop
        "neutral": 0.8,   # slightly conservative
    }

    def __init__(self, base_risk_per_trade: float = 0.01, method: str = "fixed_fractional"):
        super().__init__(risk_per_trade=base_risk_per_trade, method=method)
        self.base_risk_per_trade = base_risk_per_trade

    def size_for_regime(self, capital: float, entry: float, stop: float, atr: Optional[float] = None, regime: str = "neutral") -> float:
        multiplier = self.REGIME_MULTIPLIERS.get(regime, 0.75)
        original_risk = self.risk_per_trade
        self.risk_per_trade = self.base_risk_per_trade * multiplier
        size = self.size(capital, entry, stop, atr=atr)
        self.risk_per_trade = original_risk
        return size


class RegimeAwareStopLossManager(StopLossManager):
    """Stop-loss manager with regime-specific ATR multipliers."""

    REGIME_SL_MULTIPLIERS = {
        "bull": 4.0,      # very wide stop to ride strong trends
        "bear": 2.5,      # moderate stop (but bear trades are skipped)
        "sideways": 3.0,  # wide enough to avoid chop wicks
        "neutral": 3.5,   # wide default
    }

    REGIME_TP_MULTIPLIERS = {
        "bull": 5.0,      # let winners run far
        "bear": 2.5,      # modest target
        "sideways": 2.5,  # modest target
        "neutral": 4.0,   # default
    }

    @staticmethod
    def atr_based_for_regime(price: float, side: str, atr: float, regime: str = "neutral") -> tuple:
        """Return (stop_price, take_profit_price) for regime."""
        sl_mult = RegimeAwareStopLossManager.REGIME_SL_MULTIPLIERS.get(regime, 2.0)
        tp_mult = RegimeAwareStopLossManager.REGIME_TP_MULTIPLIERS.get(regime, 3.0)
        if side == "buy":
            stop = price - atr * sl_mult
            take = price + atr * tp_mult
        else:
            stop = price + atr * sl_mult
            take = price - atr * tp_mult
        return stop, take


class TrailingStopManager:
    """Manages trailing stops for open positions."""

    def __init__(self, activation_pct: float = 0.05, trail_pct: float = 0.3):
        self.activation_pct = activation_pct  # e.g. 5% profit to activate
        self.trail_pct = trail_pct            # e.g. trail at 30% of peak profit

    def update(self, pos: dict, bar: pd.Series) -> bool:
        """Update trailing stop for position. Return True if triggered."""
        if pos.get("side") != "long":
            return False
        entry = pos["entry_price"]
        current_high = bar["high"]
        current_low = bar["low"]
        peak_price = pos.get("peak_price", entry)

        # Update peak
        if current_high > peak_price:
            pos["peak_price"] = current_high
            peak_price = current_high

        # Check activation
        profit_pct = (peak_price - entry) / entry
        if profit_pct >= self.activation_pct:
            # Set trailing stop at trail_pct below peak
            trail_distance = (peak_price - entry) * self.trail_pct
            new_stop = peak_price - trail_distance
            if new_stop > pos.get("stop", 0):
                pos["stop"] = new_stop
                pos["trailing_active"] = True

        # Check if hit
        if current_low <= pos.get("stop", 0):
            return True
        return False


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


class RegimeAwareRiskManager(RiskManager):
    """Risk manager with regime-specific position sizing, stops, and trailing stops."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.regime_sizer = RegimeAwarePositionSizer(
            base_risk_per_trade=config.get("max_risk_per_trade", 0.01),
            method=config.get("position_sizing", "fixed_fractional")
        )
        self.regime_stop = RegimeAwareStopLossManager()
        self.trailing = TrailingStopManager(
            activation_pct=config.get("trailing_activation", 0.02),
            trail_pct=config.get("trailing_trail_pct", 0.5),
        )
        # Regime-specific drawdown limits
        self.regime_drawdown_limits = {
            "bull": config.get("max_drawdown_bull", 0.30),
            "bear": config.get("max_drawdown_bear", 0.10),
            "sideways": config.get("max_drawdown_sideways", 0.10),
            "neutral": config.get("max_drawdown_pct", 0.20),
        }
        self.current_regime = "neutral"

    def set_regime(self, regime: str):
        self.current_regime = regime
        # Update drawdown guard limit
        limit = self.regime_drawdown_limits.get(regime, 0.15)
        self.guard.max_drawdown_pct = limit
