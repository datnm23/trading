"""Aggregator — polls strategy health endpoints and builds unified state."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from loguru import logger

from backend.api.models import StrategyState, Position, TrailingStopState, SlippageSummary


STRATEGY_ENDPOINTS = [
    {"name": "RegimeEnsemble", "port": 8080},
    {"name": "EMA-Trend", "port": 8081},
    {"name": "Monthly-Breakout", "port": 8082},
]


class StateAggregator:
    """Polls all strategy bots and builds unified system."""

    def __init__(self, poll_interval: float = 5.0):
        self.poll_interval = poll_interval
        self.client = httpx.AsyncClient(timeout=5.0)
        self.strategies: Dict[str, StrategyState] = {}
        self.positions: List[Position] = []
        self.trailing_stops: List[TrailingStopState] = []
        self.slippage: List[SlippageSummary] = []
        self.equity_history: List[dict] = []
        self._latest_raw: Dict[str, dict] = {}
        self._running = False

    async def poll_strategy(self, name: str, port: int) -> Optional[StrategyState]:
        """Poll a single strategy health endpoint."""
        try:
            resp = await self.client.get(f"http://localhost:{port}/health")
            resp.raise_for_status()
            data = resp.json().get("data", {})
            self._latest_raw[name] = data

            equity = data.get("equity", 100000.0)
            initial = 100000.0

            return StrategyState(
                name=name,
                port=port,
                equity=equity,
                capital=data.get("capital", equity),
                open_positions=data.get("open_positions", 0),
                running=data.get("running", False),
                mode=data.get("mode", "paper"),
                return_pct=(equity / initial - 1.0) if initial > 0 else 0.0,
                daily_pnl=data.get("psychology", {}).get("total_pnl_today", 0.0),
                strategy_type=data.get("strategy", ""),
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.warning(f"Failed to poll {name} on port {port}: {e}")
            return None

    async def poll_all(self):
        """Poll all strategies concurrently."""
        tasks = [
            self.poll_strategy(s["name"], s["port"])
            for s in STRATEGY_ENDPOINTS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, StrategyState):
                self.strategies[res.name] = res
                # Track equity history
                self.equity_history.append({
                    "timestamp": res.timestamp.isoformat(),
                    "equity": res.equity,
                    "strategy": res.name,
                })
                # Keep only last 500 points per strategy
                self.equity_history = self.equity_history[-500:]

        # Extract positions from strategy data
        self._extract_positions()
        self._extract_trailing_stops()
        self._extract_slippage()

    def _extract_positions(self):
        """Extract positions from raw bot health data."""
        positions: List[Position] = []
        for name, data in self._latest_raw.items():
            for p in data.get("positions", []):
                positions.append(Position(
                    symbol=p.get("symbol", ""),
                    side=p.get("side", ""),
                    entry_price=p.get("entry_price", 0.0),
                    size=p.get("size", 0.0),
                    current_price=p.get("current_price"),
                    unrealized_pnl=p.get("unrealized_pnl"),
                    stop_price=p.get("stop_price"),
                    strategy=name,
                ))
        self.positions = positions

    def _extract_trailing_stops(self):
        """Placeholder."""
        self.trailing_stops = []

    def _extract_slippage(self):
        """Placeholder."""
        self.slippage = []

    def get_state(self) -> dict:
        """Return current unified state."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "strategies": [s.model_dump() for s in self.strategies.values()],
            "positions": [p.model_dump() for p in self.positions],
            "trailing_stops": [t.model_dump() for t in self.trailing_stops],
            "slippage": [s.model_dump() for s in self.slippage],
            "equity_history": self.equity_history,
            "alerts": [],
        }

    async def run_loop(self):
        """Continuous polling loop."""
        self._running = True
        while self._running:
            await self.poll_all()
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
