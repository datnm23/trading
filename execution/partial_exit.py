"""Partial Exit Manager — Scale out of positions to lock in profits."""

from dataclasses import dataclass

from loguru import logger


@dataclass
class ScaleOutLevel:
    profit_pct: float  # Profit % to trigger this level
    exit_pct: float  # % of position to close at this level
    label: str = ""


class PartialExitManager:
    """Manages scale-out (partial exits) for positions.

    Default scale-out plan:
        - 5% profit  → close 25% (recover risk)
        - 10% profit → close 25% (lock in gains)
        - 20% profit → close 25% (let 25% run)
        - 50% profit → close remaining 25%

    Usage:
        pem = PartialExitManager()
        pem.add_position(symbol, entry_price, size)
        exits = pem.check(symbol, current_price)
        for exit_size in exits:
            sell(exit_size)
    """

    DEFAULT_LEVELS = [
        ScaleOutLevel(profit_pct=0.05, exit_pct=0.25, label="Risk Recovery"),
        ScaleOutLevel(profit_pct=0.10, exit_pct=0.25, label="Profit Lock"),
        ScaleOutLevel(profit_pct=0.20, exit_pct=0.25, label="Runner Trim"),
        ScaleOutLevel(profit_pct=0.50, exit_pct=0.25, label="Final Exit"),
    ]

    def __init__(self, levels: list[ScaleOutLevel] | None = None):
        self.levels = levels or self.DEFAULT_LEVELS.copy()
        self.positions: dict[str, dict] = {}

    def add_position(
        self, symbol: str, entry_price: float, size: float, side: str = "long"
    ):
        """Register a new position for partial exit tracking."""
        self.positions[symbol] = {
            "entry_price": entry_price,
            "initial_size": size,
            "remaining_size": size,
            "side": side,
            "executed_levels": set(),
        }
        logger.info(
            f"Partial exit tracking for {symbol} | Entry: {entry_price:.2f} | Size: {size:.6f}"
        )

    def remove_position(self, symbol: str):
        """Remove position from tracking."""
        if symbol in self.positions:
            del self.positions[symbol]

    def check(self, symbol: str, current_price: float) -> list[dict]:
        """Check if any scale-out levels should trigger. Returns list of exit orders."""
        pos = self.positions.get(symbol)
        if not pos or pos["remaining_size"] <= 0:
            return []

        entry = pos["entry_price"]
        side = pos["side"]

        if side == "long":
            profit_pct = (current_price - entry) / entry
        else:
            profit_pct = (entry - current_price) / entry

        exits = []
        for level in self.levels:
            if level.profit_pct in pos["executed_levels"]:
                continue
            if profit_pct >= level.profit_pct:
                exit_size = pos["initial_size"] * level.exit_pct
                exit_size = min(exit_size, pos["remaining_size"])
                if exit_size > 0:
                    exits.append(
                        {
                            "symbol": symbol,
                            "size": exit_size,
                            "price": current_price,
                            "profit_pct": profit_pct,
                            "label": level.label,
                            "level": level.profit_pct,
                        }
                    )
                    pos["remaining_size"] -= exit_size
                    pos["executed_levels"].add(level.profit_pct)
                    logger.info(
                        f"📐 PARTIAL EXIT for {symbol} | {level.label} | "
                        f"Profit: {profit_pct:.2%} | Size: {exit_size:.6f} | Remaining: {pos['remaining_size']:.6f}"
                    )

        return exits

    def get_remaining(self, symbol: str) -> float:
        """Get remaining position size."""
        pos = self.positions.get(symbol)
        return pos["remaining_size"] if pos else 0.0

    def summary(self) -> dict[str, dict]:
        """Return summary of all tracked positions."""
        return {
            k: {
                "entry": v["entry_price"],
                "initial_size": v["initial_size"],
                "remaining": v["remaining_size"],
                "executed": list(v["executed_levels"]),
            }
            for k, v in self.positions.items()
        }
