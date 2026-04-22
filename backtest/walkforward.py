"""Walk-forward backtest engine for out-of-sample evaluation.

Simulates real-world deployment: train on past data, test on future data
that was not seen during training. No look-ahead bias.

Usage:
    engine = WalkForwardEngine(
        strategy_factory=...,
        risk_manager=...,
        train_window_bars=365,
        test_window_bars=90,
    )
    results = engine.run(df, start_idx=365)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Dict, Optional

import pandas as pd
import numpy as np
from loguru import logger

from backtest.engine import BacktestEngine, BacktestResult, Trade
from risk.manager import RiskManager
from strategies.base import BaseStrategy


@dataclass
class WalkForwardResult:
    """Result of one walk-forward window."""
    period_label: str
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_bars: int
    test_bars: int
    metrics: dict
    trades: list
    equity_curve: pd.Series
    model_checkpoint: Optional[str] = None


class WalkForwardEngine:
    """Run walk-forward analysis with expanding or rolling train window.

    Args:
        strategy_factory: Callable[[], BaseStrategy] — creates fresh strategy
        risk_manager: RiskManager instance
        train_window_bars: Number of bars for training/warmup
        test_window_bars: Number of bars per test period
        initial_capital: Starting capital
        commission: Commission rate
        slippage: Slippage rate
    """

    def __init__(
        self,
        strategy_factory: Callable[[], BaseStrategy],
        risk_manager: RiskManager,
        train_window_bars: int = 365,
        test_window_bars: int = 90,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ):
        self.strategy_factory = strategy_factory
        self.risk_manager = risk_manager
        self.train_window_bars = train_window_bars
        self.test_window_bars = test_window_bars
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.results: List[WalkForwardResult] = []

    def run(self, data: pd.DataFrame, start_idx: Optional[int] = None) -> List[WalkForwardResult]:
        """Run walk-forward on full dataset.

        Args:
            data: Full OHLCV DataFrame with datetime index
            start_idx: Bar index to start first test period (default: train_window_bars)

        Returns:
            List of WalkForwardResult, one per test period
        """
        if start_idx is None:
            start_idx = self.train_window_bars

        total_bars = len(data)
        current = start_idx

        while current + self.test_window_bars <= total_bars:
            train_end = current
            train_start = max(0, train_end - self.train_window_bars)
            test_end = min(current + self.test_window_bars, total_bars)

            train_df = data.iloc[train_start:train_end]
            test_df = data.iloc[train_end:test_end]

            period_label = self._make_label(data.index[train_end], data.index[test_end - 1])
            logger.info(
                f"Walk-forward | {period_label} | "
                f"Train: {len(train_df)} bars | Test: {len(test_df)} bars"
            )

            result = self._run_period(train_df, test_df, period_label)
            self.results.append(result)

            current += self.test_window_bars

        return self.results

    def _run_period(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, label: str
    ) -> WalkForwardResult:
        """Run single walk-forward period."""
        # Fresh strategy for each period (no leakage from previous period)
        strategy = self.strategy_factory()

        # BacktestEngine requires 100 bars for warmup and loops from bar 100.
        # If test_df has < 100 bars the loop would be empty, so prepend the
        # last 100 bars of train data.  Trades only happen during the loop,
        # which covers exactly the test period.
        warmup_needed = 100
        train_tail = train_df.iloc[-min(warmup_needed, len(train_df)):]
        combined = pd.concat([train_tail, test_df])

        # Reset drawdown guard so each period starts fresh
        self.risk_manager.guard.reset()

        engine = BacktestEngine(
            initial_capital=self.initial_capital,
            commission=self.commission,
            slippage=self.slippage,
        )
        result = engine.run(combined, strategy, self.risk_manager)

        # Force-close any open positions at the end of the test period so
        # that each period's trade count reflects round-trips.
        if engine.positions:
            last_bar = test_df.iloc[-1]
            for pos in list(engine.positions):
                exit_price = last_bar["close"] * (1 - engine.slippage)
                pnl = (exit_price - pos["entry_price"]) * pos["size"]
                pnl -= pos["size"] * exit_price * engine.commission
                engine.trades.append(Trade(
                    entry_time=pos["entry_time"],
                    exit_time=last_bar.name,
                    symbol=pos["symbol"],
                    side=pos["side"],
                    entry_price=pos["entry_price"],
                    exit_price=exit_price,
                    size=pos["size"],
                    pnl=pnl,
                    exit_reason="period_end",
                ))
                engine.positions.remove(pos)

        # Recalculate total cost including forced-close trades
        total_cost = 0.0
        for t in engine.trades:
            entry_commission = t.size * t.entry_price * engine.commission
            exit_commission = t.size * t.exit_price * engine.commission
            entry_slippage = t.size * t.entry_price * engine.slippage / (1 + engine.slippage)
            exit_slippage = t.size * t.exit_price * engine.slippage / (1 - engine.slippage)
            total_cost += entry_commission + exit_commission + entry_slippage + exit_slippage

        gross_return = result.total_return + (total_cost / self.initial_capital if self.initial_capital else 0)
        total_trades = len(engine.trades)

        return WalkForwardResult(
            period_label=label,
            train_start=train_df.index[0],
            train_end=train_df.index[-1],
            test_start=test_df.index[0],
            test_end=test_df.index[-1],
            train_bars=len(train_df),
            test_bars=len(test_df),
            metrics={
                "total_return": result.total_return,
                "gross_return": gross_return,
                "total_cost": total_cost,
                "avg_cost_per_trade": total_cost / total_trades if total_trades else 0,
                "sharpe": result.sharpe,
                "max_drawdown": result.max_drawdown,
                "winrate": result.winrate,
                "profit_factor": result.profit_factor,
                "total_trades": total_trades,
            },
            trades=[
                {
                    "entry_time": t.entry_time.isoformat() if hasattr(t.entry_time, 'isoformat') else str(t.entry_time),
                    "exit_time": t.exit_time.isoformat() if t.exit_time and hasattr(t.exit_time, 'isoformat') else None,
                    "symbol": t.symbol,
                    "side": t.side,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "size": t.size,
                    "pnl": t.pnl,
                    "exit_reason": t.exit_reason,
                }
                for t in engine.trades
            ],
            equity_curve=result.equity_curve,
        )

    @staticmethod
    def _make_label(start: datetime, end: datetime) -> str:
        return f"{start.strftime('%Y-%m-%d')}_{end.strftime('%Y-%m-%d')}"

    def summary(self) -> pd.DataFrame:
        """Return summary DataFrame of all periods."""
        rows = []
        for r in self.results:
            row = dict(r.metrics)
            row["period"] = r.period_label
            row["train_bars"] = r.train_bars
            row["test_bars"] = r.test_bars
            rows.append(row)
        return pd.DataFrame(rows)

    def save(self, path: str):
        """Save results to JSON."""
        data = {
            "meta": {
                "train_window_bars": self.train_window_bars,
                "test_window_bars": self.test_window_bars,
                "initial_capital": self.initial_capital,
                "commission": self.commission,
                "slippage": self.slippage,
                "periods_count": len(self.results),
                "generated_at": datetime.now().isoformat(),
            },
            "periods": [
                {
                    "period_label": r.period_label,
                    "train_start": r.train_start.isoformat(),
                    "train_end": r.train_end.isoformat(),
                    "test_start": r.test_start.isoformat(),
                    "test_end": r.test_end.isoformat(),
                    "metrics": r.metrics,
                    "model_checkpoint": r.model_checkpoint,
                }
                for r in self.results
            ],
            "aggregate": {
                "total_return": sum(r.metrics["total_return"] for r in self.results),
                "avg_sharpe": np.mean([r.metrics["sharpe"] for r in self.results]),
                "avg_max_dd": np.mean([r.metrics["max_drawdown"] for r in self.results]),
                "total_trades": sum(r.metrics["total_trades"] for r in self.results),
            },
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Walk-forward results saved to {path}")
