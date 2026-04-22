#!/usr/bin/env python3
"""Run all strategies in parallel for real-time comparison.

Usage:
    python scripts/run_all_strategies.py

Each strategy runs in its own process with:
  - Separate health port (8080, 8081, 8082)
  - Separate log file
  - Shared PostgreSQL journal
  - Same symbol list and timeframe
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root is in path
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load .env so Telegram tokens are available
dotenv_path = project_root / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"Loaded .env from {dotenv_path}")
else:
    print("Warning: .env not found, Telegram alerts may be disabled")

STRATEGIES = [
    {"name": "RegimeEnsemble", "port": 8080, "log": "logs/bot_regime.log"},
    {"name": "EMA-Trend", "port": 8081, "log": "logs/bot_ema.log"},
    {"name": "Monthly-Breakout", "port": 8082, "log": "logs/bot_breakout.log"},
]

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
CONFIG = "config/local.yaml"
MODE = "paper"


def start_strategy(name: str, port: int, log_file: str) -> subprocess.Popen:
    """Start a single strategy bot as a subprocess."""
    cmd = [
        sys.executable, "-m", "execution.live_trading",
        "--config", CONFIG,
        "--mode", MODE,
        "--strategy", name,
        "--health-port", str(port),
    ]
    # Add symbols as separate args if module supports it
    # live_trading.py main() doesn't accept --symbols, only --symbol
    # We run with default symbols from config

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    f = open(log_file, "a")
    f.write(f"\n{'='*60}\n")
    f.write(f"Starting {name} on port {port}\n")
    f.write(f"{'='*60}\n")
    f.flush()

    proc = subprocess.Popen(
        cmd,
        stdout=f,
        stderr=subprocess.STDOUT,
        cwd=str(project_root),
        env=os.environ,
    )
    return proc


def main():
    print("=" * 60)
    print("HYBRID TRADING — Multi-Strategy Realtime Comparison")
    print("=" * 60)

    processes = []
    for s in STRATEGIES:
        print(f"\n▶ Starting {s['name']} on health port {s['port']}...")
        proc = start_strategy(s["name"], s["port"], s["log"])
        processes.append({"name": s["name"], "port": s["port"], "proc": proc, "log": s["log"]})
        time.sleep(2)  # stagger startups to avoid DB lock conflicts

    print("\n" + "=" * 60)
    print("ALL STRATEGIES STARTED")
    print("=" * 60)
    for p in processes:
        print(f"  {p['name']:20s}  PID:{p['proc'].pid:6d}  Health:http://localhost:{p['port']}/health")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all strategies\n")

    # Write PID file for management
    pid_file = Path("all_strategies.pid")
    pid_file.write_text("\n".join(str(p["proc"].pid) for p in processes))

    try:
        while True:
            time.sleep(5)
            # Check if any process died
            for p in processes:
                if p["proc"].poll() is not None:
                    print(f"⚠️  {p['name']} exited with code {p['proc'].returncode}")
    except KeyboardInterrupt:
        print("\n\nStopping all strategies...")
        for p in processes:
            print(f"  Killing {p['name']} (PID {p['proc'].pid})...")
            p["proc"].terminate()
            try:
                p["proc"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                p["proc"].kill()
        print("All stopped.")
        pid_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
