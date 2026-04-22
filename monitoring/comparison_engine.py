"""Strategy Comparison Engine — Real-time multi-strategy performance tracker.

Usage:
    from monitoring.comparison_engine import StrategyComparison
    comp = StrategyComparison()
    comp.poll_all()          # Fetch latest from all bots
    print(comp.leaderboard()) # Print ranking table
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import requests
from loguru import logger


@dataclass
class StrategySnapshot:
    """Single snapshot of a running strategy bot."""
    name: str
    port: int
    timestamp: datetime
    equity: float
    capital: float
    open_positions: int
    running: bool
    mode: str = "paper"
    daily_pnl: float = 0.0
    total_return_pct: float = 0.0
    drawdown_pct: float = 0.0
    raw: dict = field(default_factory=dict)


class StrategyComparison:
    """Poll multiple strategy health endpoints and compare performance."""

    DEFAULT_STRATEGIES = [
        {"name": "RegimeEnsemble", "port": 8080},
        {"name": "EMA-Trend", "port": 8081},
        {"name": "Monthly-Breakout", "port": 8082},
    ]

    INITIAL_CAPITAL = 100000.0

    def __init__(self, strategies: Optional[List[dict]] = None, initial_capital: float = 100000.0):
        self.strategies = strategies or self.DEFAULT_STRATEGIES.copy()
        self.initial_capital = initial_capital
        self.snapshots: Dict[str, StrategySnapshot] = {}
        self.history: Dict[str, List[StrategySnapshot]] = {s["name"]: [] for s in self.strategies}

    def _fetch_health(self, port: int) -> Optional[dict]:
        """Fetch health endpoint from a bot."""
        try:
            resp = requests.get(f"http://localhost:{port}/health", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Health check failed on port {port}: {e}")
            return None

    def poll(self, name: str, port: int) -> Optional[StrategySnapshot]:
        """Poll a single strategy bot."""
        data = self._fetch_health(port)
        if data is None:
            return None

        d = data.get("data", {})
        equity = d.get("equity", self.initial_capital)
        total_return = (equity / self.initial_capital) - 1.0

        snap = StrategySnapshot(
            name=name,
            port=port,
            timestamp=datetime.now(),
            equity=equity,
            capital=d.get("capital", equity),
            open_positions=d.get("open_positions", 0),
            running=d.get("running", False),
            mode=d.get("mode", "paper"),
            daily_pnl=d.get("psychology", {}).get("total_pnl_today", 0.0),
            total_return_pct=total_return,
            drawdown_pct=d.get("psychology", {}).get("drawdown_pct", 0.0),
            raw=d,
        )
        self.snapshots[name] = snap
        self.history[name].append(snap)
        # Keep only last 1000 snapshots per strategy
        if len(self.history[name]) > 1000:
            self.history[name] = self.history[name][-1000:]
        return snap

    def poll_all(self) -> Dict[str, StrategySnapshot]:
        """Poll all strategy bots."""
        for s in self.strategies:
            self.poll(s["name"], s["port"])
        return self.snapshots

    def leaderboard(self) -> List[dict]:
        """Return sorted leaderboard by total return."""
        rows = []
        for name, snap in self.snapshots.items():
            rows.append({
                "strategy": name,
                "equity": snap.equity,
                "return_pct": snap.total_return_pct,
                "daily_pnl": snap.daily_pnl,
                "open_positions": snap.open_positions,
                "running": snap.running,
                "last_update": snap.timestamp.strftime("%H:%M:%S"),
            })
        rows.sort(key=lambda x: x["return_pct"], reverse=True)
        return rows

    def format_table(self) -> str:
        """Format leaderboard as a readable ASCII table."""
        rows = self.leaderboard()
        if not rows:
            return "No strategy data available."

        lines = [
            "",
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║                    STRATEGY COMPARISON LEADERBOARD                           ║",
            f"║                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║",
            "╠════════════════════╦══════════════╦═══════════╦════════════╦═════════╦═══════╣",
            "║ Strategy           ║ Equity       ║ Return    ║ Daily P&L  ║ Pos     ║ Status║",
            "╠════════════════════╬══════════════╬═══════════╬════════════╬═════════╬═══════╣",
        ]

        for r in rows:
            status = "🟢" if r["running"] else "🔴"
            lines.append(
                f"║ {r['strategy']:18s} ║ "
                f"${r['equity']:>11,.2f} ║ "
                f"{r['return_pct']:>+7.2%} ║ "
                f"${r['daily_pnl']:>9,.2f} ║ "
                f"{r['open_positions']:>7d} ║ "
                f"{status:5s} ║"
            )

        lines.append("╚════════════════════╩══════════════╩═══════════╩════════════╩═════════╩═══════╝")
        lines.append("")
        return "\n".join(lines)

    def save_to_postgres(self, db_url: str):
        """Save current snapshots to PostgreSQL for historical tracking."""
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS strategy_comparison (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    strategy VARCHAR(50) NOT NULL,
                    equity NUMERIC(20, 2),
                    capital NUMERIC(20, 2),
                    total_return_pct NUMERIC(10, 4),
                    daily_pnl NUMERIC(20, 2),
                    open_positions INTEGER,
                    running BOOLEAN,
                    raw_data JSONB
                )
            """)

            for name, snap in self.snapshots.items():
                cur.execute("""
                    INSERT INTO strategy_comparison
                    (strategy, equity, capital, total_return_pct, daily_pnl, open_positions, running, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    snap.name,
                    snap.equity,
                    snap.capital,
                    snap.total_return_pct,
                    snap.daily_pnl,
                    snap.open_positions,
                    snap.running,
                    json.dumps(snap.raw),
                ))

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Saved {len(self.snapshots)} strategy snapshots to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to save to PostgreSQL: {e}")

    def get_equity_curves(self) -> Dict[str, List[tuple]]:
        """Return equity curves for plotting: {strategy: [(timestamp, equity), ...]}."""
        curves = {}
        for name, snaps in self.history.items():
            curves[name] = [(s.timestamp, s.equity) for s in snaps]
        return curves


def main():
    """CLI: Real-time strategy comparison."""
    import time
    import argparse

    parser = argparse.ArgumentParser(description="Compare running strategies in real-time")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds")
    parser.add_argument("--db-url", default=None, help="PostgreSQL URL to save snapshots")
    args = parser.parse_args()

    comp = StrategyComparison()
    db_url = args.db_url or "postgresql://trader:trading123@localhost:5432/trading_journal"

    print("\n🔍 Strategy Comparison Monitor")
    print("=" * 60)
    print("Polling strategies every {} seconds...".format(args.interval))
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            comp.poll_all()
            print(comp.format_table())

            if args.db_url is not None:
                comp.save_to_postgres(db_url)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n\nStopped.")


if __name__ == "__main__":
    main()
