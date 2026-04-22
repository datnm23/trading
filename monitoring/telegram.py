"""Telegram alerting system for trading signals, errors, and drawdown.

Setup:
    1. Create bot via @BotFather, get token
    2. Send /start to bot, get chat ID from:
       https://api.telegram.org/bot<TOKEN>/getUpdates
    3. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
"""

import os
from typing import Optional, List
from datetime import datetime

import requests
from loguru import logger


class TelegramAlerter:
    """Send alerts via Telegram Bot API."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        enabled: bool = True,
    ):
        self.token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = enabled and bool(self.token) and bool(self.chat_id)

        if self.enabled:
            logger.info(f"Telegram alerter enabled for chat {self.chat_id}")
        else:
            logger.warning("Telegram alerter disabled (missing token or chat_id)")

    def _send(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled:
            logger.debug(f"[TELEGRAM suppressed] {text[:100]}...")
            return False

        try:
            url = f"{self.BASE_URL.format(token=self.token)}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_signal(
        self,
        symbol: str,
        side: str,
        price: float,
        size: float,
        strategy: str = "",
        reason: str = "",
    ):
        """Alert on new trading signal."""
        emoji = "🟢" if side.lower() == "buy" else "🔴"
        text = (
            f"<b>{emoji} SIGNAL: {side.upper()} {symbol}</b>\n\n"
            f"Price: <code>{price:,.2f}</code>\n"
            f"Size: <code>{size:.6f}</code>\n"
            f"Strategy: {strategy or 'N/A'}\n"
            f"Reason: {reason or 'N/A'}\n"
            f"Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )
        self._send(text)

    def send_trade_closed(
        self,
        symbol: str,
        side: str,
        entry: float,
        exit_price: float,
        pnl: float,
        pnl_pct: float,
        exit_reason: str = "",
    ):
        """Alert on trade close."""
        emoji = "✅" if pnl > 0 else "❌"
        text = (
            f"<b>{emoji} TRADE CLOSED: {symbol}</b>\n\n"
            f"Side: {side.upper()}\n"
            f"Entry: <code>{entry:,.2f}</code>\n"
            f"Exit: <code>{exit_price:,.2f}</code>\n"
            f"P&L: <code>${pnl:,.2f}</code> ({pnl_pct:+.2%})\n"
            f"Reason: {exit_reason or 'N/A'}\n"
            f"Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )
        self._send(text)

    def send_drawdown_alert(
        self,
        current_drawdown: float,
        max_allowed: float,
        equity: float,
        peak: float,
    ):
        """Alert when drawdown exceeds threshold."""
        text = (
            f"<b>⚠️ DRAWDOWN ALERT</b>\n\n"
            f"Current DD: <code>{current_drawdown:.2%}</code>\n"
            f"Max Allowed: <code>{max_allowed:.2%}</code>\n"
            f"Peak Equity: <code>${peak:,.2f}</code>\n"
            f"Current Equity: <code>${equity:,.2f}</code>\n\n"
            f"<b>Trading halted. Manual review required.</b>"
        )
        self._send(text)

    def send_error(self, error_message: str, context: str = ""):
        """Alert on critical system error."""
        text = (
            f"<b>🔥 SYSTEM ERROR</b>\n\n"
            f"Context: {context or 'General'}\n"
            f"Message: <pre>{error_message[:500]}</pre>\n"
            f"Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )
        self._send(text)

    def send_daily_summary(
        self,
        trades_today: int,
        pnl_today: float,
        winrate_today: float,
        equity: float,
        open_positions: int,
    ):
        """Send end-of-day trading summary."""
        emoji = "📈" if pnl_today >= 0 else "📉"
        text = (
            f"<b>{emoji} DAILY SUMMARY</b>\n\n"
            f"Trades: <code>{trades_today}</code>\n"
            f"P&L: <code>${pnl_today:,.2f}</code>\n"
            f"Winrate: <code>{winrate_today:.1%}</code>\n"
            f"Equity: <code>${equity:,.2f}</code>\n"
            f"Open Positions: <code>{open_positions}</code>\n"
            f"Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )
        self._send(text)

    def send_startup(self, mode: str, symbols: List[str], strategies: List[str]):
        """Send bot startup notification."""
        text = (
            f"<b>🚀 TRADING BOT STARTED</b>\n\n"
            f"Mode: <code>{mode.upper()}</code>\n"
            f"Symbols: <code>{', '.join(symbols)}</code>\n"
            f"Strategies: <code>{', '.join(strategies)}</code>\n"
            f"Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
        )
        self._send(text)

    def test(self) -> bool:
        """Send test message to verify configuration."""
        return self._send("<b>🧪 Test alert from Hybrid Trading System</b>\nConfiguration OK.")
