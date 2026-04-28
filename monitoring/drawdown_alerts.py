"""Drawdown alerts — bilingual warning before circuit breaker triggers.

Sends Telegram alerts when drawdown approaches dangerous levels,
giving the trader time to intervene before automatic halt.
"""

from datetime import datetime, timedelta

from loguru import logger

from monitoring.telegram import TelegramAlerter


class DrawdownAlertManager:
    """Warn when drawdown exceeds threshold but before halt.

    Example:
        - Warning at 10% DD → alert sent
        - Halt at 18% DD (bull) → circuit breaker stops bot
    """

    def __init__(
        self,
        alerter: TelegramAlerter | None = None,
        enabled: bool = True,
        warning_pct: float = 0.10,
        cooldown_hours: float = 4.0,
    ):
        self.alerter = alerter
        self.enabled = enabled and (alerter is not None and alerter.enabled)
        self.warning_pct = warning_pct
        self.cooldown = timedelta(hours=cooldown_hours)
        self._last_alert: datetime | None = None
        self._peak_equity: float = 0.0

    def check(self, equity: float) -> bool:
        """Check drawdown and send alert if warning threshold crossed.

        Returns True if warning was sent.
        """
        if not self.enabled or equity <= 0:
            return False

        # Update peak
        if equity > self._peak_equity:
            self._peak_equity = equity
            return False

        if self._peak_equity <= 0:
            return False

        drawdown = (self._peak_equity - equity) / self._peak_equity

        # Only alert if above warning threshold
        if drawdown < self.warning_pct:
            return False

        # Cooldown check
        now = datetime.now()
        if self._last_alert and (now - self._last_alert) < self.cooldown:
            return False

        self._send_alert(drawdown, equity)
        self._last_alert = now
        return True

    def _send_alert(self, drawdown: float, equity: float):
        """Send bilingual drawdown warning."""
        text = (
            f"🇺🇸 <b>⚠️ DRAWDOWN WARNING</b>\n\n"
            f"Current DD: <code>{drawdown:.2%}</code>\n"
            f"Warning at: <code>{self.warning_pct:.2%}</code>\n"
            f"Peak Equity: <code>${self._peak_equity:,.2f}</code>\n"
            f"Current Equity: <code>${equity:,.2f}</code>\n\n"
            f"<b>Action needed:</b> Review positions or reduce size.\n"
            f"Circuit breaker will trigger at higher DD.\n\n"
            f"🇻🇳 <b>⚠️ CẢNH BÁO RÚT LÙI VỐN</b>\n\n"
            f"Rút lùi hiện tại: <code>{drawdown:.2%}</code>\n"
            f"Ngưỡng cảnh báo: <code>{self.warning_pct:.2%}</code>\n"
            f"Vốn đỉnh: <code>${self._peak_equity:,.2f}</code>\n"
            f"Vốn hiện tại: <code>${equity:,.2f}</code>\n\n"
            f"<b>Cần hành động:</b> Xem lại vị thế hoặc giảm size.\n"
            f"Circuit breaker sẽ kích hoạt ở mức rút lùi cao hơn.\n\n"
            f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )

        if self.alerter:
            self.alerter._send(text)
            logger.warning(
                f"Drawdown warning sent: {drawdown:.2%} (threshold {self.warning_pct:.2%})"
            )
