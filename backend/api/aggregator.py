"""Aggregator — polls strategy health endpoints and builds unified state."""

import asyncio
import os
from datetime import UTC, datetime

import httpx
from loguru import logger

from backend.api.graduation_service import GraduationService
from backend.api.models import (
    Position,
    SlippageSummary,
    StrategyState,
    TrailingStopState,
)
from backend.api.trades_service import TradesService

STRATEGY_ENDPOINTS = [
    {
        "name": "RegimeEnsemble",
        "host": os.environ.get("BOT_HOST", "trading-bot"),
        "port": 8080,
    },
]


class StateAggregator:
    """Polls all strategy bots and builds unified system."""

    def __init__(self, poll_interval: float = 5.0):
        self.poll_interval = poll_interval
        self.client = httpx.AsyncClient(timeout=5.0)
        self.strategies: dict[str, StrategyState] = {}
        self.positions: list[Position] = []
        self.trailing_stops: list[TrailingStopState] = []
        self.slippage: list[SlippageSummary] = []
        self.partial_exits: list[dict] = []
        self.equity_history: list[dict] = []
        self._latest_raw: dict[str, dict] = {}
        self._running = False
        self._trades_service = TradesService()
        self._graduation_service = GraduationService()
        self._sub_stats: dict[str, dict] = {}
        self._graduation_metrics: dict = {}

    async def poll_strategy(
        self, name: str, host: str, port: int
    ) -> StrategyState | None:
        """Poll a single strategy health endpoint."""
        try:
            resp = await self.client.get(f"http://{host}:{port}/health")
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
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
            logger.warning(f"Failed to poll {name} on port {port}: {e}")
            return None

    def _build_sub_strategies(self, ensemble_data: dict) -> list[StrategyState]:
        """Synthesize 3 sub-strategy cards from the single ensemble bot."""
        equity = ensemble_data.get("equity", 100000.0)
        ensemble_data.get("capital", equity)
        initial = 100000.0
        running = ensemble_data.get("running", False)
        mode = ensemble_data.get("mode", "paper")
        ensemble_data.get("open_positions", 0)
        (equity / initial - 1.0) if initial > 0 else 0.0
        ensemble_data.get("psychology", {}).get("total_pnl_today", 0.0)
        sub = ensemble_data.get("sub_strategy", {})
        sub_signals = sub.get("sub_signals", {})
        current_regime = ensemble_data.get("current_regime", "unknown")
        directional = ensemble_data.get("directional_regime", "unknown")

        sub_defs = [
            {"name": "EMA-Trend", "type": "ema", "regime": "trending"},
            {"name": "Monthly-Breakout", "type": "breakout", "regime": "trending"},
            {"name": "Grid-MeanReversion", "type": "grid", "regime": "ranging"},
        ]

        # Count actual open positions per sub-strategy from position metadata
        position_counts: dict[str, int] = {}
        for p in ensemble_data.get("positions", []):
            source = p.get("meta", {}).get("ensemble_source", "unknown")
            position_counts[source] = position_counts.get(source, 0) + 1

        results = []
        for sd in sub_defs:
            active_signal = sub_signals.get(sd["type"])
            is_active_regime = current_regime == sd["regime"]

            # Use real trade stats if available; otherwise show no return
            stats = self._sub_stats.get(sd["type"], {})
            realized_pnl = stats.get("total_pnl", 0.0)
            sub_trade_count = stats.get("trade_count", 0)
            sub_winrate = stats.get("winrate", 0.0)

            # Add unrealized P&L from open positions belonging to this sub-strategy
            unrealized_pnl = sum(
                (p.get("unrealized_pnl") or 0)
                for p in ensemble_data.get("positions", [])
                if p.get("meta", {}).get("ensemble_source") == sd["type"]
            )
            total_pnl = realized_pnl + unrealized_pnl

            # Each sub-strategy gets 1/3 of initial capital as notional allocation
            sub_initial = initial / 3
            sub_equity = sub_initial + total_pnl
            sub_return = (total_pnl / sub_initial) if sub_initial > 0 else 0.0

            results.append(
                StrategyState(
                    name=sd["name"],
                    port=8080,
                    equity=sub_equity,
                    capital=sub_equity,
                    open_positions=position_counts.get(sd["type"], 0),
                    running=running,
                    mode=mode,
                    return_pct=sub_return,
                    daily_pnl=0.0,
                    strategy_type=sd["type"],
                    timestamp=datetime.now(UTC),
                    meta={
                        "active_signal": active_signal,
                        "is_active_regime": is_active_regime,
                        "current_regime": current_regime,
                        "directional_regime": directional,
                        "wiki_alignment": sub.get("wiki_alignment", 0.0),
                        "wiki_action": sub.get("wiki_action", "no_signal"),
                        "final_decision": sub.get("final_decision", "no_signal"),
                        "rejection_reasons": sub.get("rejection_reasons", []),
                        "trade_count": sub_trade_count,
                        "winrate": sub_winrate,
                        "total_pnl": total_pnl,
                        "realized_pnl": realized_pnl,
                        "unrealized_pnl": unrealized_pnl,
                    },
                )
            )
        return results

    async def poll_all(self):
        """Poll all strategies concurrently."""
        tasks = [
            self.poll_strategy(s["name"], s["host"], s["port"])
            for s in STRATEGY_ENDPOINTS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, StrategyState):
                self.strategies[res.name] = res
                # Track equity history
                self.equity_history.append(
                    {
                        "timestamp": res.timestamp.isoformat(),
                        "equity": res.equity,
                        "strategy": res.name,
                    }
                )
                # Keep only last 500 points per strategy
                self.equity_history = self.equity_history[-500:]

        # Fetch sub-strategy trade stats (run sync DB query in thread pool)
        try:
            loop = asyncio.get_running_loop()
            self._sub_stats = await loop.run_in_executor(
                None, self._trades_service.get_sub_strategy_stats
            )
        except Exception as e:
            logger.warning(f"Failed to fetch sub-strategy stats: {e}")

        # Fetch graduation metrics
        try:
            loop = asyncio.get_running_loop()
            self._graduation_metrics = await loop.run_in_executor(
                None, self._graduation_service.compute_metrics
            )
        except Exception as e:
            logger.warning(f"Failed to fetch graduation metrics: {e}")

        # Synthesize sub-strategies from ensemble
        ensemble_raw = self._latest_raw.get("RegimeEnsemble", {})
        if ensemble_raw:
            sub_strategies = self._build_sub_strategies(ensemble_raw)
            for ss in sub_strategies:
                self.strategies[ss.name] = ss

        # Extract positions from strategy data
        self._extract_positions()
        self._extract_trailing_stops()
        self._extract_slippage()
        self._extract_partial_exits()

    def _extract_positions(self):
        """Extract positions from raw bot health data."""
        positions: list[Position] = []
        for name, data in self._latest_raw.items():
            for p in data.get("positions", []):
                positions.append(
                    Position(
                        symbol=p.get("symbol", ""),
                        side=p.get("side", ""),
                        entry_price=p.get("entry_price", 0.0),
                        size=p.get("size", 0.0),
                        current_price=p.get("current_price"),
                        unrealized_pnl=p.get("unrealized_pnl"),
                        stop_price=p.get("stop_price"),
                        strategy=name,
                        entry_time=p.get("entry_time"),
                        meta=p.get("meta"),
                    )
                )
        self.positions = positions

    def _extract_trailing_stops(self):
        """Extract trailing stop states from raw bot health data."""
        stops: list[TrailingStopState] = []
        for name, data in self._latest_raw.items():
            for symbol, info in data.get("trailing_stops", {}).items():
                stops.append(
                    TrailingStopState(
                        symbol=symbol,
                        entry_price=info.get("entry", 0.0),
                        peak_price=info.get("peak", 0.0),
                        current_stop=info.get("current_stop", 0.0),
                        activated=info.get("activated", False),
                        profit_pct=info.get("profit_pct", 0.0),
                    )
                )
        self.trailing_stops = stops

    def _extract_slippage(self):
        """Extract slippage summaries from raw bot health data."""
        slippage: list[SlippageSummary] = []
        for name, data in self._latest_raw.items():
            for symbol, info in data.get("slippage", {}).items():
                slippage.append(
                    SlippageSummary(
                        symbol=symbol,
                        trades=info.get("trades", 0),
                        avg_slippage_pct=info.get("avg_slippage_pct", 0.0),
                        max_slippage_pct=info.get("max_slippage_pct", 0.0),
                        total_cost=info.get("total_slippage_cost", 0.0),
                    )
                )
        self.slippage = slippage

    def _extract_partial_exits(self):
        """Extract partial exit states from raw bot health data."""
        from backend.api.models import PartialExitState

        exits: list[PartialExitState] = []
        for name, data in self._latest_raw.items():
            for symbol, info in data.get("partial_exits", {}).items():
                exits.append(
                    PartialExitState(
                        symbol=symbol,
                        entry=info.get("entry", 0.0),
                        initial_size=info.get("initial_size", 0.0),
                        remaining=info.get("remaining", 0.0),
                        executed_count=len(info.get("executed", [])),
                    )
                )
        self.partial_exits = exits

    def get_state(self) -> dict:
        """Return current unified state."""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "strategies": [s.model_dump() for s in self.strategies.values()],
            "positions": [p.model_dump() for p in self.positions],
            "trailing_stops": [t.model_dump() for t in self.trailing_stops],
            "slippage": [s.model_dump() for s in self.slippage],
            "partial_exits": [p.model_dump() for p in self.partial_exits],
            "equity_history": self.equity_history,
            "alerts": [],
            "graduation": self._graduation_metrics,
            "sub_strategy": self._latest_raw.get("RegimeEnsemble", {}).get(
                "sub_strategy", {}
            ),
            "current_regime": self._latest_raw.get("RegimeEnsemble", {}).get(
                "current_regime", "unknown"
            ),
            "directional_regime": self._latest_raw.get("RegimeEnsemble", {}).get(
                "directional_regime", "unknown"
            ),
            "regime_distribution": self._latest_raw.get("RegimeEnsemble", {}).get(
                "regime_distribution", {}
            ),
        }

    async def run_loop(self):
        """Continuous polling loop."""
        self._running = True
        while self._running:
            await self.poll_all()
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
