"""Daily Report Generator — Automated P&L, metrics, and insight reports."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

import pandas as pd
from loguru import logger


class DailyReportGenerator:
    """Generates daily trading reports from journal data.

    Usage:
        report = DailyReportGenerator(journal_db_url)
        summary = report.generate()
        print(summary.to_text())
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv(
            "TRADING_DB_URL",
            "postgresql://trader:trading123@localhost:5432/trading_journal"
        )

    def _get_connection(self):
        """Return PostgreSQL connection."""
        import psycopg2
        return psycopg2.connect(self.db_url)

    def get_today_trades(self) -> pd.DataFrame:
        """Fetch today's trades."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        query = f"""
            SELECT * FROM trades
            WHERE timestamp >= '{today} 00:00:00'
            ORDER BY timestamp DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_today_snapshots(self) -> pd.DataFrame:
        """Fetch today's equity snapshots."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        query = f"""
            SELECT * FROM equity_snapshots
            WHERE timestamp >= '{today} 00:00:00'
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def generate(self) -> "DailyReport":
        """Generate full daily report."""
        trades = self.get_today_trades()
        snapshots = self.get_today_snapshots()

        report = DailyReport(
            date=datetime.now().strftime("%Y-%m-%d"),
            total_trades=len(trades),
            wins=len(trades[trades["pnl"] > 0]) if not trades.empty else 0,
            losses=len(trades[trades["pnl"] <= 0]) if not trades.empty else 0,
            total_pnl=trades["pnl"].sum() if not trades.empty else 0.0,
            avg_trade=trades["pnl"].mean() if not trades.empty else 0.0,
            max_profit=trades["pnl"].max() if not trades.empty else 0.0,
            max_loss=trades["pnl"].min() if not trades.empty else 0.0,
            start_equity=snapshots["equity"].iloc[0] if not snapshots.empty else 0.0,
            end_equity=snapshots["equity"].iloc[-1] if not snapshots.empty else 0.0,
            strategies=trades["strategy"].unique().tolist() if not trades.empty else [],
        )
        return report

    def generate_and_notify(self, alerter=None):
        """Generate report and send via Telegram if alerter provided."""
        report = self.generate()
        text = report.to_telegram()
        logger.info("Daily report generated")
        if alerter:
            try:
                alerter._send(text)
            except Exception as e:
                logger.warning(f"Failed to send daily report: {e}")
        return report


class DailyReport:
    """Immutable daily report data."""

    def __init__(self, date: str, total_trades: int, wins: int, losses: int,
                 total_pnl: float, avg_trade: float, max_profit: float, max_loss: float,
                 start_equity: float, end_equity: float, strategies: List[str]):
        self.date = date
        self.total_trades = total_trades
        self.wins = wins
        self.losses = losses
        self.total_pnl = total_pnl
        self.avg_trade = avg_trade
        self.max_profit = max_profit
        self.max_loss = max_loss
        self.start_equity = start_equity
        self.end_equity = end_equity
        self.strategies = strategies

        self.winrate = wins / total_trades if total_trades > 0 else 0.0
        self.profit_factor = abs(total_pnl / max_loss) if max_loss != 0 else float("inf")
        self.return_pct = (end_equity / start_equity - 1) if start_equity > 0 else 0.0

    def to_text(self) -> str:
        """Format as readable text."""
        lines = [
            "",
            "╔══════════════════════════════════════════════════════════════╗",
            f"║          DAILY TRADING REPORT — {self.date}                 ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║ Total Trades:  {self.total_trades:4d}                                      ║",
            f"║ Wins:          {self.wins:4d}  |  Losses:      {self.losses:4d}                  ║",
            f"║ Winrate:       {self.winrate:>6.1%}                                      ║",
            f"║ Total P&L:     ${self.total_pnl:>10,.2f}                                ║",
            f"║ Avg Trade:     ${self.avg_trade:>10,.2f}                                ║",
            f"║ Max Profit:    ${self.max_profit:>10,.2f}                                ║",
            f"║ Max Loss:      ${self.max_loss:>10,.2f}                                ║",
            f"║ Start Equity:  ${self.start_equity:>10,.2f}                                ║",
            f"║ End Equity:    ${self.end_equity:>10,.2f}                                ║",
            f"║ Return:        {self.return_pct:>+7.2%}                                      ║",
            f"║ Strategies:    {', '.join(self.strategies)[:30]:30s}              ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
        ]
        return "\n".join(lines)

    def to_telegram(self) -> str:
        """Format as Telegram HTML message."""
        emoji = "🟢" if self.total_pnl >= 0 else "🔴"
        return (
            f"<b>{emoji} DAILY REPORT — {self.date}</b>\n\n"
            f"Trades: <code>{self.wins}W / {self.losses}L</code> | "
            f"Winrate: <code>{self.winrate:.1%}</code>\n"
            f"Total P&L: <code>${self.total_pnl:,.2f}</code>\n"
            f"Avg Trade: <code>${self.avg_trade:,.2f}</code>\n"
            f"Return: <code>{self.return_pct:+.2%}</code>\n\n"
            f"Equity: <code>${self.start_equity:,.0f}</code> → <code>${self.end_equity:,.0f}</code>\n"
            f"Strategies: <code>{', '.join(self.strategies)}</code>"
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate daily trading report")
    parser.add_argument("--db-url", help="PostgreSQL URL")
    parser.add_argument("--db-path", default="./data/journal.db", help="SQLite path")
    args = parser.parse_args()

    gen = DailyReportGenerator(db_url=args.db_url, db_path=args.db_path)
    report = gen.generate()
    print(report.to_text())


if __name__ == "__main__":
    main()
