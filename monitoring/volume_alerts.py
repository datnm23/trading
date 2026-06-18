"""Volume spike alerts for abnormal trading activity.

Detects when volume on the current bar exceeds historical average
by a configurable multiplier (e.g., 2x, 3x). Sends bilingual
Telegram alerts when unusual volume is detected.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
from loguru import logger

from monitoring.telegram import TelegramAlerter


@dataclass
class VolumeAlertState:
    """Track volume alert state per symbol."""

    last_alerted: datetime | None = None
    cooldown_hours: float = 4.0


class VolumeAlertManager:
    """Monitor volume and alert on abnormal spikes.

    Compares current bar volume against N-bar SMA.
    Alerts when current volume exceeds multiplier threshold.
    """

    def __init__(
        self,
        alerter: TelegramAlerter | None = None,
        enabled: bool = True,
        lookback_bars: int = 20,
        multiplier: float = 2.5,
        cooldown_hours: float = 4.0,
    ):
        self.alerter = alerter
        self.enabled = enabled and (alerter is not None and alerter.enabled)
        self.lookback_bars = lookback_bars
        self.multiplier = multiplier
        self.cooldown = timedelta(hours=cooldown_hours)
        self._states: dict[str, VolumeAlertState] = {}
        self._history: dict[str, list[float]] = {}  # recent volume history per symbol

    def check(self, symbol: str, df: pd.DataFrame):
        """Check if current bar volume is abnormal.

        Args:
            symbol: Trading pair symbol
            df: OHLCV DataFrame with 'volume' column
        """
        if not self.enabled or df.empty or "volume" not in df.columns:
            return

        if len(df) < self.lookback_bars + 1:
            return

        # Get current and historical volume
        current_volume = df["volume"].iloc[-1]
        hist_volume = df["volume"].iloc[-self.lookback_bars - 1 : -1]

        if hist_volume.empty or hist_volume.mean() <= 0:
            return

        avg_volume = hist_volume.mean()
        ratio = current_volume / avg_volume

        # Store in history
        if symbol not in self._history:
            self._history[symbol] = []
        self._history[symbol].append(current_volume)
        if len(self._history[symbol]) > self.lookback_bars * 2:
            self._history[symbol].pop(0)

        # Check if spike
        if ratio < self.multiplier:
            return

        # Check cooldown
        state = self._states.get(symbol, VolumeAlertState())
        now = datetime.now()
        if state.last_alerted and (now - state.last_alerted) < self.cooldown:
            return

        # Send alert
        self._send_alert(symbol, current_volume, avg_volume, ratio)
        state.last_alerted = now
        self._states[symbol] = state

    def _send_alert(self, symbol: str, current: float, average: float, ratio: float):
        """Send bilingual volume spike alert."""
        emoji = "🚨" if ratio >= 3.0 else "⚠️"

        text = (
            f"{emoji} <b>VOLUME SPIKE — {symbol}</b>\n\n"
            f"Current Volume: <code>{current:,.0f}</code>\n"
            f"{self.lookback_bars}-bar Avg: <code>{average:,.0f}</code>\n"
            f"Ratio: <code>{ratio:.1f}x</code>\n\n"
            f"{emoji} <b>BÙNG NỔ KHỐI LƯỢNG — {symbol}</b>\n\n"
            f"Khối lượng hiện tại: <code>{current:,.0f}</code>\n"
            f"Trung bình {self.lookback_bars} bar: <code>{average:,.0f}</code>\n"
            f"Tỷ lệ: <code>{ratio:.1f}x</code>\n\n"
            f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )

        if self.alerter:
            self.alerter._send(text)
            logger.warning(
                f"Volume spike alert for {symbol}: {ratio:.1f}x avg ({current:,.0f} vs {average:,.0f})"
            )
