"""Trailing Stop Manager — Auto-adjusts stop-loss as price moves favorably."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from loguru import logger


@dataclass
class TrailingStopConfig:
    activation_pct: float = 0.05      # 5% profit to activate trailing
    trail_pct: float = 0.30           # Trail at 30% of peak profit
    min_profit_lock: float = 0.02     # Lock in 2% minimum profit once activated


class TrailingStopManager:
    """Manages trailing stops for open positions.

    Usage:
        ts = TrailingStopManager(config)
        ts.add_position(symbol, entry_price, initial_stop)
        new_stop = ts.update(symbol, current_price)
        if new_stop and price <= new_stop:
            exit_position()
    """

    def __init__(self, config: Optional[TrailingStopConfig] = None):
        self.config = config or TrailingStopConfig()
        self.positions: Dict[str, dict] = {}

    def add_position(self, symbol: str, entry_price: float, initial_stop: float, side: str = "long"):
        """Register a new position for trailing stop tracking."""
        self.positions[symbol] = {
            "entry_price": entry_price,
            "initial_stop": initial_stop,
            "current_stop": initial_stop,
            "peak_price": entry_price,
            "side": side,
            "activated": False,
            "highest_profit_pct": 0.0,
        }
        logger.info(f"Trailing stop registered for {symbol} | Entry: {entry_price:.2f} | Initial stop: {initial_stop:.2f}")

    def remove_position(self, symbol: str):
        """Remove position from tracking."""
        if symbol in self.positions:
            del self.positions[symbol]

    def update(self, symbol: str, current_price: float) -> Optional[float]:
        """Update trailing stop for a position. Returns new stop level if changed."""
        pos = self.positions.get(symbol)
        if not pos:
            return None

        entry = pos["entry_price"]
        side = pos["side"]

        if side == "long":
            profit_pct = (current_price - entry) / entry
            if current_price > pos["peak_price"]:
                pos["peak_price"] = current_price
        else:
            profit_pct = (entry - current_price) / entry
            if current_price < pos["peak_price"]:
                pos["peak_price"] = current_price

        # Check activation
        if not pos["activated"]:
            if profit_pct >= self.config.activation_pct:
                pos["activated"] = True
                pos["highest_profit_pct"] = profit_pct
                logger.info(f"🎯 Trailing stop ACTIVATED for {symbol} | Profit: {profit_pct:.2%}")
            return None

        # Update highest profit
        if profit_pct > pos["highest_profit_pct"]:
            pos["highest_profit_pct"] = profit_pct

        # Calculate new trailing stop
        if side == "long":
            # Trail at trail_pct below peak profit
            peak_profit_distance = pos["peak_price"] - entry
            trail_distance = peak_profit_distance * self.config.trail_pct
            new_stop = pos["peak_price"] - trail_distance

            # Ensure minimum profit lock
            min_stop = entry * (1 + self.config.min_profit_lock)
            new_stop = max(new_stop, min_stop)

            # Only move stop up
            if new_stop > pos["current_stop"]:
                old_stop = pos["current_stop"]
                pos["current_stop"] = new_stop
                logger.info(f"🔄 Trailing stop MOVED for {symbol} | {old_stop:.2f} → {new_stop:.2f} | Peak: {pos['peak_price']:.2f}")
                return new_stop
        else:
            # Short position
            peak_profit_distance = entry - pos["peak_price"]
            trail_distance = peak_profit_distance * self.config.trail_pct
            new_stop = pos["peak_price"] + trail_distance

            min_stop = entry * (1 - self.config.min_profit_lock)
            new_stop = min(new_stop, min_stop)

            if new_stop < pos["current_stop"]:
                old_stop = pos["current_stop"]
                pos["current_stop"] = new_stop
                logger.info(f"🔄 Trailing stop MOVED for {symbol} | {old_stop:.2f} → {new_stop:.2f}")
                return new_stop

        return None

    def should_exit(self, symbol: str, current_price: float) -> bool:
        """Check if price has hit trailing stop."""
        pos = self.positions.get(symbol)
        if not pos or not pos["activated"]:
            return False

        if pos["side"] == "long":
            return current_price <= pos["current_stop"]
        return current_price >= pos["current_stop"]

    def get_stop(self, symbol: str) -> Optional[float]:
        """Get current stop level."""
        pos = self.positions.get(symbol)
        return pos["current_stop"] if pos else None

    def summary(self) -> Dict[str, dict]:
        """Return summary of all tracked positions."""
        return {k: {
            "entry": v["entry_price"],
            "current_stop": v["current_stop"],
            "peak": v["peak_price"],
            "activated": v["activated"],
            "profit_pct": v["highest_profit_pct"],
        } for k, v in self.positions.items()}
