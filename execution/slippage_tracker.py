"""Slippage Tracker — Measures and alerts on execution slippage."""

from dataclasses import dataclass
from datetime import datetime

from loguru import logger


@dataclass
class SlippageRecord:
    timestamp: datetime
    symbol: str
    side: str
    expected_price: float
    filled_price: float
    size: float
    slippage_pct: float
    slippage_amount: float


class SlippageTracker:
    """Tracks execution slippage and alerts when excessive.

    Usage:
        tracker = SlippageTracker(warning_threshold_pct=0.001)
        tracker.record(symbol="BTC/USDT", side="buy", expected=79000, filled=79050, size=0.1)
        if tracker.last_slippage(symbol) > 0.001:
            alert("High slippage!")
    """

    def __init__(self, warning_threshold_pct: float = 0.001, max_records: int = 1000):
        self.warning_threshold_pct = warning_threshold_pct
        self.max_records = max_records
        self.records: list[SlippageRecord] = []
        self.by_symbol: dict[str, list[SlippageRecord]] = {}

    def record(
        self,
        symbol: str,
        side: str,
        expected_price: float,
        filled_price: float,
        size: float,
    ):
        """Record a fill and calculate slippage."""
        if expected_price <= 0 or filled_price <= 0:
            return

        if side.lower() in ("buy", "long"):
            slippage_pct = (filled_price - expected_price) / expected_price
        else:
            slippage_pct = (expected_price - filled_price) / expected_price

        slippage_amount = abs(filled_price - expected_price) * size

        record = SlippageRecord(
            timestamp=datetime.now(),
            symbol=symbol,
            side=side,
            expected_price=expected_price,
            filled_price=filled_price,
            size=size,
            slippage_pct=slippage_pct,
            slippage_amount=slippage_amount,
        )

        self.records.append(record)
        if symbol not in self.by_symbol:
            self.by_symbol[symbol] = []
        self.by_symbol[symbol].append(record)

        # Trim old records
        if len(self.records) > self.max_records:
            old = self.records.pop(0)
            self.by_symbol[old.symbol].pop(0)

        # Log warning
        if abs(slippage_pct) > self.warning_threshold_pct:
            logger.warning(
                f"⚠️  HIGH SLIPPAGE on {symbol} {side} | "
                f"Expected: {expected_price:.2f} | Filled: {filled_price:.2f} | "
                f"Slippage: {slippage_pct:+.4%} (${slippage_amount:.2f})"
            )
        else:
            logger.info(
                f"📊 Slippage on {symbol} {side} | "
                f"Expected: {expected_price:.2f} | Filled: {filled_price:.2f} | "
                f"Slippage: {slippage_pct:+.4%}"
            )

    def last_slippage(self, symbol: str) -> float | None:
        """Get last slippage % for a symbol."""
        recs = self.by_symbol.get(symbol, [])
        return recs[-1].slippage_pct if recs else None

    def avg_slippage(self, symbol: str, n: int = 10) -> float | None:
        """Get average slippage over last N trades."""
        recs = self.by_symbol.get(symbol, [])
        if not recs:
            return None
        recent = recs[-n:]
        return sum(r.slippage_pct for r in recent) / len(recent)

    def summary(self) -> dict[str, dict]:
        """Return slippage summary by symbol."""
        result = {}
        for sym, recs in self.by_symbol.items():
            if recs:
                result[sym] = {
                    "trades": len(recs),
                    "avg_slippage_pct": sum(r.slippage_pct for r in recs) / len(recs),
                    "max_slippage_pct": max(r.slippage_pct for r in recs),
                    "min_slippage_pct": min(r.slippage_pct for r in recs),
                    "total_slippage_cost": sum(r.slippage_amount for r in recs),
                }
        return result
