#!/usr/bin/env python3
"""CLI tool to compare all running strategies in real-time.

Usage:
    python scripts/compare_strategies.py
    python scripts/compare_strategies.py --watch --interval 10
    python scripts/compare_strategies.py --save --db-url postgresql://...
"""

import sys
import time
import argparse
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from monitoring.comparison_engine import StrategyComparison


def main():
    parser = argparse.ArgumentParser(description="Compare running trading strategies")
    parser.add_argument("--watch", "-w", action="store_true", help="Continuous polling mode")
    parser.add_argument("--interval", "-i", type=int, default=10, help="Polling interval in seconds (default: 10)")
    parser.add_argument("--save", "-s", action="store_true", help="Save snapshots to PostgreSQL")
    parser.add_argument("--db-url", default="postgresql://trader:trading123@localhost:5432/trading_journal", help="PostgreSQL URL")
    args = parser.parse_args()

    comp = StrategyComparison()

    if not args.watch:
        # One-shot mode
        comp.poll_all()
        print(comp.format_table())
        if args.save:
            comp.save_to_postgres(args.db_url)
        return

    # Watch mode
    print("\n🔍 Strategy Comparison Monitor — Watch Mode")
    print("=" * 60)
    print(f"Polling every {args.interval}s | Press Ctrl+C to stop\n")

    try:
        while True:
            comp.poll_all()
            # Clear screen (cross-platform-ish)
            print("\033[2J\033[H", end="")
            print(comp.format_table())

            if args.save:
                comp.save_to_postgres(args.db_url)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n\nStopped.")


if __name__ == "__main__":
    main()
