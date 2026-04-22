#!/usr/bin/env python3
"""Query trading journal for P&L, winrate, and performance metrics.

Supports both SQLite and PostgreSQL backends.

Usage:
    # Query PostgreSQL (default for running bot)
    python scripts/query_journal.py

    # Query specific symbol
    python scripts/query_journal.py --symbol BTC/USDT

    # Query SQLite file directly
    python scripts/query_journal.py --db data/journal.db

    # Export to CSV
    python scripts/query_journal.py --export trades.csv
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from journal.trade_logger import TradeLogger


def format_currency(val: float) -> str:
    return f"${val:,.2f}"


def format_pct(val: float) -> str:
    return f"{val:.2%}"


def print_summary(logger: TradeLogger, symbol: str = None):
    """Print comprehensive performance summary."""
    summary = logger.trade_summary(symbol=symbol)

    print("=" * 60)
    print("📊 TRADING PERFORMANCE SUMMARY")
    print("=" * 60)

    if summary["count"] == 0:
        print("\n❌ No trades found in journal.")
        return

    print(f"\n{'Metric':<25} {'Value':>20}")
    print("-" * 46)
    print(f"{'Total Trades':<25} {summary['count']:>20}")
    print(f"{'Total P&L':<25} {format_currency(summary['total_pnl']):>20}")
    print(f"{'Avg P&L per Trade':<25} {format_currency(summary['avg_pnl']):>20}")
    print(f"{'Winrate':<25} {format_pct(summary['winrate']):>20}")
    print(f"{'Profit Factor':<25} {summary['profit_factor']:>20.2f}")
    print(f"{'Avg Win':<25} {format_currency(summary['avg_win']):>20}")
    print(f"{'Avg Loss':<25} {format_currency(summary['avg_loss']):>20}")
    print(f"{'Max Win':<25} {format_currency(summary['max_win']):>20}")
    print(f"{'Max Loss':<25} {format_currency(summary['max_loss']):>20}")

    # Recent trades
    print("\n" + "=" * 60)
    print("📝 RECENT TRADES (last 10)")
    print("=" * 60)
    trades = logger.get_trades(symbol=symbol, limit=10)
    if trades:
        print(f"\n{'Time':<20} {'Symbol':<12} {'Side':<6} {'P&L':>12} {'P&L%':>8} {'Reason':<15}")
        print("-" * 80)
        for t in trades:
            emoji = "🟢" if t.pnl > 0 else "🔴" if t.pnl < 0 else "⚪"
            time_str = t.timestamp.strftime("%Y-%m-%d %H:%M") if isinstance(t.timestamp, datetime) else str(t.timestamp)[:16]
            print(
                f"{time_str:<20} {t.symbol:<12} {t.side:<6} "
                f"{emoji}{format_currency(t.pnl):>10} {format_pct(t.pnl_pct):>8} {t.exit_reason:<15}"
            )
    else:
        print("\nNo trades found.")

    # Emotion distribution
    emotions = logger.emotion_distribution()
    if emotions:
        print("\n" + "=" * 60)
        print("🎭 EMOTION DISTRIBUTION")
        print("=" * 60)
        for emotion, count in sorted(emotions.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {emotion:<15} {count:>3} {bar}")

    # Equity snapshots
    print("\n" + "=" * 60)
    print("📈 EQUITY SNAPSHOTS (last 5)")
    print("=" * 60)
    snaps = logger.get_snapshots(limit=5)
    if snaps:
        print(f"\n{'Time':<20} {'Equity':>15} {'Cash':>15} {'Positions':>10} {'DD%':>8}")
        print("-" * 72)
        for s in snaps:
            time_str = s.timestamp.strftime("%Y-%m-%d %H:%M") if isinstance(s.timestamp, datetime) else str(s.timestamp)[:16]
            print(
                f"{time_str:<20} {format_currency(s.equity):>15} "
                f"{format_currency(s.cash):>15} {s.open_positions:>10} {format_pct(s.drawdown_pct):>8}"
            )
    else:
        print("\nNo snapshots found.")

    print("\n" + "=" * 60)


def export_trades(logger: TradeLogger, path: str, symbol: str = None):
    """Export trades to CSV."""
    logger.export_trades_csv(path, symbol=symbol)
    print(f"✅ Exported to {path}")


def main():
    parser = argparse.ArgumentParser(description="Query trading journal")
    parser.add_argument("--db", default=None, help="SQLite db path (default: use PostgreSQL)")
    parser.add_argument("--pg-url", default="postgresql://trader:trading123@localhost:5432/trading_journal",
                        help="PostgreSQL connection URL")
    parser.add_argument("--symbol", help="Filter by symbol (e.g. BTC/USDT)")
    parser.add_argument("--export", help="Export trades to CSV file")
    args = parser.parse_args()

    if args.db:
        logger = TradeLogger(db_path=args.db)
        print(f"📁 Using SQLite: {args.db}\n")
    else:
        logger = TradeLogger(db_url=args.pg_url)
        print(f"🐘 Using PostgreSQL: {args.pg_url}\n")

    if args.export:
        export_trades(logger, args.export, symbol=args.symbol)
    else:
        print_summary(logger, symbol=args.symbol)


if __name__ == "__main__":
    main()
