"""Price level alerts for important price thresholds.

Supports bilingual alerts (English + Vietnamese) via Telegram.
Tracks round numbers, percentage levels, and key support/resistance.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from loguru import logger

from monitoring.telegram import TelegramAlerter


@dataclass
class PriceLevel:
    """A price level to watch."""
    price: float
    label_en: str
    label_vn: str
    last_alerted: Optional[datetime] = None
    cooldown_hours: float = 1.0


class PriceAlertManager:
    """Monitor real-time prices and alert when approaching important levels.

    Uses CCXT fetch_ticker() for live price instead of bar close.
    Automatically generates round-number and percentage-based levels
    relative to current price. Prevents spam with per-level cooldowns.
    """

    def __init__(
        self,
        alerter: Optional[TelegramAlerter] = None,
        connector=None,
        enabled: bool = True,
        threshold_pct: float = 0.008,  # 0.8% — alert when within 0.8% of level
    ):
        self.alerter = alerter
        self.connector = connector
        self.enabled = enabled and (alerter is not None and alerter.enabled)
        self.threshold_pct = threshold_pct
        self._levels: Dict[str, List[PriceLevel]] = {}
        self._last_price: Dict[str, float] = {}
        self._initialized: Dict[str, bool] = {}

    def _generate_levels(self, current_price: float, symbol: str) -> List[PriceLevel]:
        """Generate key price levels based on current price."""
        levels = []

        # Determine step size based on price magnitude
        if current_price >= 50000:  # BTC
            step = 5000
        elif current_price >= 1000:  # ETH
            step = 100
        elif current_price >= 100:   # SOL, etc
            step = 10
        else:
            step = 1

        # Round numbers above and below
        base = int(current_price / step) * step
        for offset in [-step, 0, step, 2 * step, -2 * step]:
            price = base + offset
            if price > 0:
                direction = "Support" if price < current_price else "Resistance"
                direction_vn = "Hỗ trợ" if price < current_price else "Kháng cự"
                levels.append(PriceLevel(
                    price=float(price),
                    label_en=f"Round Number {direction}",
                    label_vn=f"Số tròn {direction_vn}",
                ))

        # Percentage levels
        for pct in [0.02, 0.05, 0.10]:
            for sign in [1, -1]:
                price = current_price * (1 + sign * pct)
                if sign > 0:
                    label_en = f"+{pct:.0%} Resistance"
                    label_vn = f"Kháng cự +{pct:.0%}"
                else:
                    label_en = f"-{pct:.0%} Support"
                    label_vn = f"Hỗ trợ -{pct:.0%}"
                levels.append(PriceLevel(
                    price=price,
                    label_en=label_en,
                    label_vn=label_vn,
                ))

        return levels

    def check(self, symbol: str, fallback_price: float):
        """Check real-time price against all levels and alert if close.

        Uses CCXT fetch_ticker() for live price. Falls back to provided price
        if ticker fetch fails (e.g. in paper mode without connector).
        """
        if not self.enabled:
            return

        # Fetch real-time price from exchange
        current_price = fallback_price
        if self.connector:
            try:
                ticker = self.connector.fetch_ticker(symbol)
                if ticker and ticker.get("last"):
                    current_price = float(ticker["last"])
                    logger.debug(f"Real-time price for {symbol}: ${current_price:,.2f}")
            except Exception as e:
                logger.warning(f"Failed to fetch real-time price for {symbol}: {e}")

        # Initialize levels on first call
        if symbol not in self._initialized or not self._initialized[symbol]:
            self._levels[symbol] = self._generate_levels(current_price, symbol)
            self._initialized[symbol] = True
            logger.info(f"PriceAlertManager initialized for {symbol} at ${current_price:,.2f}")

        self._last_price[symbol] = current_price
        now = datetime.now()

        for level in self._levels[symbol]:
            # Skip if on cooldown
            if level.last_alerted and (now - level.last_alerted) < timedelta(hours=level.cooldown_hours):
                continue

            distance_pct = abs(current_price - level.price) / level.price
            if distance_pct <= self.threshold_pct:
                # Price is close to this level — send alert
                self._send_alert(symbol, current_price, level, distance_pct)
                level.last_alerted = now

    def _send_alert(self, symbol: str, current_price: float, level: PriceLevel, distance_pct: float):
        """Send bilingual price alert via Telegram."""
        direction = "above" if current_price > level.price else "below"
        direction_pct = ((current_price - level.price) / level.price) * 100

        emoji = "🟢" if direction_pct > 0 else "🔴"
        arrow = "↑" if direction_pct > 0 else "↓"

        text = (
            f"🇺🇸 <b>PRICE ALERT — {symbol}</b>\n\n"
            f"Current: <code>${current_price:,.2f}</code>\n"
            f"Level: <code>${level.price:,.2f}</code>\n"
            f"Distance: <code>{direction_pct:+.2f}%</code> {arrow}\n"
            f"Type: <code>{level.label_en}</code>\n\n"
            f"🇻🇳 <b>CẢNH BÁO GIÁ — {symbol}</b>\n\n"
            f"Giá hiện tại: <code>${current_price:,.2f}</code>\n"
            f"Mức: <code>${level.price:,.2f}</code>\n"
            f"Khoảng cách: <code>{direction_pct:+.2f}%</code> {arrow}\n"
            f"Loại: <code>{level.label_vn}</code>\n\n"
            f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )

        if self.alerter:
            self.alerter._send(text)
            logger.info(f"Price alert sent for {symbol} at ${current_price:,.2f} near ${level.price:,.2f}")

    def get_status(self, symbol: str) -> Dict:
        """Return current alert status for a symbol."""
        levels = self._levels.get(symbol, [])
        current_price = self._last_price.get(symbol, 0)
        return {
            "symbol": symbol,
            "current_price": current_price,
            "levels_tracked": len(levels),
            "levels": [
                {
                    "price": l.price,
                    "label": l.label_en,
                    "last_alerted": l.last_alerted.isoformat() if l.last_alerted else None,
                }
                for l in levels
            ],
        }
