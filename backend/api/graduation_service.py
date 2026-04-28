"""Paper trading graduation monitor — computes metrics and checks graduation gates."""

import os
from datetime import UTC, datetime, timedelta

import psycopg2
from loguru import logger
from psycopg2.extras import RealDictCursor

from monitoring.telegram import TelegramAlerter


class GraduationService:
    """Compute paper trading graduation metrics from trade history.

    Criteria:
        - 30+ days of trading activity
        - Positive net return
        - Max drawdown < 10%
        - Sharpe ratio > 0.5
        - Winrate > 40%
    """

    def __init__(self, db_url: str | None = None, initial_capital: float = 100000.0):
        self.db_url = db_url or os.environ.get("TRADING_DB_URL")
        self.initial_capital = initial_capital
        self._alerter = TelegramAlerter()
        self._notified_path = os.environ.get(
            "GRADUATION_NOTIFY_FILE", ".graduation_notified"
        )
        self._notified = self._load_notified()

    def _load_notified(self) -> bool:
        """Check if graduation alert was already sent (persisted across restarts)."""
        try:
            return os.path.exists(self._notified_path)
        except Exception:
            return False

    def _save_notified(self):
        """Persist notification state to prevent duplicate alerts on restart."""
        try:
            with open(self._notified_path, "w") as f:
                f.write(datetime.now(UTC).isoformat())
        except Exception as e:
            logger.warning(f"Failed to persist graduation notification: {e}")

    def reset_notification(self):
        """Clear persisted notification state (for testing or re-graduation)."""
        self._notified = False
        try:
            if os.path.exists(self._notified_path):
                os.remove(self._notified_path)
        except Exception as e:
            logger.warning(f"Failed to reset graduation notification: {e}")

    def _connect(self):
        return psycopg2.connect(self.db_url)

    def compute_metrics(self) -> dict:
        """Return graduation metrics based on last 30 days of trades."""
        if not self.db_url:
            return self._empty_result("No database configured")

        cutoff = datetime.now(UTC) - timedelta(days=30)
        cutoff_str = cutoff.isoformat()

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Fetch all trades in last 30 days
            cur.execute(
                """
                SELECT timestamp, pnl, pnl_pct, exit_price, entry_price
                FROM trades
                WHERE timestamp >= %s
                  AND raw_metadata IS NOT NULL
                  AND raw_metadata::text != ''
                  AND raw_metadata::text != '{}'
                ORDER BY timestamp ASC
            """,
                (cutoff_str,),
            )
            trades = cur.fetchall()

            if not trades:
                return self._empty_result("No trades in last 30 days")

            # Days with trading activity
            trade_dates = set()
            for t in trades:
                ts = t["timestamp"]
                if isinstance(ts, datetime):
                    trade_dates.add(ts.date())
                else:
                    try:
                        trade_dates.add(datetime.fromisoformat(str(ts)).date())
                    except Exception:
                        pass
            days_traded = len(trade_dates)

            # Return %
            total_pnl = sum(float(t["pnl"] or 0) for t in trades)
            return_pct = (
                (total_pnl / self.initial_capital * 100)
                if self.initial_capital > 0
                else 0.0
            )

            # Winrate
            wins = sum(1 for t in trades if float(t["pnl"] or 0) > 0)
            winrate = (wins / len(trades) * 100) if trades else 0.0

            # Max drawdown from equity curve (synthetic from cumulative P&L)
            cumulative = 0.0
            peak = 0.0
            max_dd = 0.0
            for t in trades:
                cumulative += float(t["pnl"] or 0)
                if cumulative > peak:
                    peak = cumulative
                dd = peak - cumulative
                if dd > max_dd:
                    max_dd = dd
            max_drawdown_pct = (
                (max_dd / self.initial_capital * 100)
                if self.initial_capital > 0
                else 0.0
            )

            # Sharpe ratio (daily returns)
            daily_pnls: dict[str, float] = {}
            for t in trades:
                ts = t["timestamp"]
                if isinstance(ts, datetime):
                    day = ts.date().isoformat()
                else:
                    try:
                        day = datetime.fromisoformat(str(ts)).date().isoformat()
                    except Exception:
                        continue
                daily_pnls[day] = daily_pnls.get(day, 0.0) + float(t["pnl"] or 0)

            daily_returns = [pnl / self.initial_capital for pnl in daily_pnls.values()]
            if len(daily_returns) > 1:
                import statistics

                avg_return = statistics.mean(daily_returns)
                std_return = statistics.stdev(daily_returns)
                sharpe = (
                    (avg_return / std_return * (252**0.5)) if std_return > 0 else 0.0
                )
            else:
                sharpe = 0.0

            # Gates
            gates = {
                "days_traded": days_traded >= 30,
                "return_positive": return_pct > 0,
                "drawdown": max_drawdown_pct < 10.0,
                "sharpe": sharpe > 0.5,
                "winrate": winrate > 40.0,
            }
            approved = all(gates.values())

            result = {
                "days_traded": days_traded,
                "days_required": 30,
                "return_pct": round(return_pct, 2),
                "max_drawdown_pct": round(max_drawdown_pct, 2),
                "sharpe": round(sharpe, 3),
                "winrate": round(winrate, 2),
                "trade_count": len(trades),
                "total_pnl": round(total_pnl, 2),
                "gates": gates,
                "approved": approved,
                "message": (
                    "Graduation criteria met!"
                    if approved
                    else "Paper trading in progress"
                ),
            }

            # Send Telegram alert once when approved
            if approved and not self._notified:
                self._send_graduation_alert(result)
                self._notified = True
                self._save_notified()

            return result

        except Exception as e:
            logger.error(f"Graduation metrics computation failed: {e}")
            return self._empty_result(f"Error: {e}")
        finally:
            conn.close()

    def _empty_result(self, message: str) -> dict:
        return {
            "days_traded": 0,
            "days_required": 30,
            "return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe": 0.0,
            "winrate": 0.0,
            "trade_count": 0,
            "total_pnl": 0.0,
            "gates": {
                "days_traded": False,
                "return_positive": False,
                "drawdown": False,
                "sharpe": False,
                "winrate": False,
            },
            "approved": False,
            "message": message,
        }

    def _send_graduation_alert(self, result: dict):
        """Send Telegram alert when graduation criteria are met."""
        text = (
            "🎓 *Paper Trading Graduation Criteria Met!*\n\n"
            f"📊 Return: {result['return_pct']:.2f}%\n"
            f"📉 Max DD: {result['max_drawdown_pct']:.2f}%\n"
            f"⚡ Sharpe: {result['sharpe']:.3f}\n"
            f"🏆 Winrate: {result['winrate']:.1f}%\n"
            f"📅 Days: {result['days_traded']}/30\n"
            f"💰 Total P&L: ${result['total_pnl']:,.2f}\n\n"
            "✅ System is approved for live trading graduation."
        )
        try:
            self._alerter.send(text)
            logger.info("Graduation alert sent via Telegram")
        except Exception as e:
            logger.warning(f"Failed to send graduation alert: {e}")
