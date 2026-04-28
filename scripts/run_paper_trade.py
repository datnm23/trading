#!/usr/bin/env python3
"""Run paper trading with RegimeEnsemble strategy.

Simple wrapper to start paper trading on Binance testnet.

Usage:
    python scripts/run_paper_trade.py

The bot will:
    1. Fetch latest 4h bars from Binance
    2. Run RegimeEnsemble strategy with wiki validation
    3. Execute signals in paper mode (no real money)
    4. Send Telegram alerts on trades / errors
    5. Log all activity to journal DB
    6. Expose health check on port 8080

To stop: Ctrl+C
"""

# ruff: noqa: E402

import argparse
import sys
from pathlib import Path

sys.path.insert(0, "/home/datnm/projects/trading")

# Load .env if present
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from execution.live_trading import LiveTradingEngine, load_config
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy


def main():
    parser = argparse.ArgumentParser(description="Paper Trading — RegimeEnsemble")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
        help="Trading pairs (default: BTC/USDT ETH/USDT SOL/USDT)",
    )
    parser.add_argument("--timeframe", default="4h", help="Candle timeframe")
    parser.add_argument("--config", default="config/system.yaml", help="Config path")
    args = parser.parse_args()

    config = load_config(args.config)

    # Force paper mode
    config["system"]["mode"] = "paper"
    config["execution"]["paper"] = True

    # Use 4h timeframe for RegimeEnsemble
    config["data"]["timeframe"] = args.timeframe

    # Find RegimeEnsemble strategy config by name (robust lookup)
    regime_config = None
    for entry in config["strategies"]["registry"]:
        if entry["name"] == "RegimeEnsemble":
            regime_config = entry
            break
    if regime_config is None:
        raise ValueError("RegimeEnsemble not found in config/strategies/registry")

    strategy = RegimeEnsembleStrategy(params=regime_config["params"])

    engine = LiveTradingEngine(
        config=config,
        strategy=strategy,
        mode="paper",
        symbols=args.symbols,
    )

    print("=" * 60)
    print("PAPER TRADING STARTED")
    print("=" * 60)
    print(f"Symbols:    {', '.join(args.symbols)}")
    print(f"Timeframe:  {args.timeframe}")
    print("Strategy:   RegimeEnsemble (+86% walk-forward proven)")
    print("Mode:       PAPER (no real money)")
    print("Health:     http://localhost:8080/health")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        engine.run()
    except KeyboardInterrupt:
        print("\nStopping paper trading...")
        engine.stop()


if __name__ == "__main__":
    main()
