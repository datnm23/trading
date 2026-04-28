"""Simple event-driven backtest engine."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from loguru import logger

from risk.manager import RegimeAwareRiskManager, RiskManager
from strategies.base import BaseStrategy, Signal, StrategyContext


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp | None = None
    symbol: str = ""
    side: str = ""  # "long" | "short"
    entry_price: float = 0.0
    exit_price: float = 0.0
    size: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    trades: list = field(default_factory=list)
    total_return: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    winrate: float = 0.0
    profit_factor: float = 0.0
    total_cost: float = 0.0


class BacktestEngine:
    """Event-driven backtest engine."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.capital = initial_capital
        self.equity = initial_capital
        self.positions = []
        self.trades = []
        self.equity_history = []

    def run(
        self, data: pd.DataFrame, strategy: BaseStrategy, risk_manager: RiskManager
    ) -> BacktestResult:
        """Run backtest on historical data."""
        strategy.reset()
        strategy.warmup(data.iloc[:100])

        for i in range(100, len(data)):
            bar = data.iloc[i]
            history = data.iloc[: i + 1]

            # Check stop-loss and trailing stops for open positions
            self._check_stops(bar, risk_manager)

            context = StrategyContext(
                symbol=data.name if hasattr(data, "name") else "UNKNOWN",
                bar=bar,
                history=history,
                account={"capital": self.capital, "equity": self.equity},
                positions=self.positions,
            )

            # Check risk guard
            status = risk_manager.check(self.capital, self.equity, self.positions)
            if status["halted"]:
                logger.warning("Drawdown guard triggered. Halting.")
                break

            signal = strategy.on_bar(context)
            if signal:
                self._process_signal(signal, bar, risk_manager, status)

            # Update equity with mark-to-market
            self._update_equity(bar)
            self.equity_history.append({"timestamp": bar.name, "equity": self.equity})

        return self._build_result()

    def _process_signal(
        self, signal: Signal, bar: pd.Series, risk_manager: RiskManager, status: dict
    ):
        regime = (
            signal.meta.get("directional_regime", "neutral")
            if signal.meta
            else "neutral"
        )

        # Update risk manager regime if regime-aware
        if isinstance(risk_manager, RegimeAwareRiskManager):
            risk_manager.set_regime(regime)

        if signal.side == "buy":
            if not status["exposure_ok"]:
                return
            entry_price = bar["close"] * (1 + self.slippage)
            atr = signal.meta.get("atr") if signal.meta else None

            if isinstance(risk_manager, RegimeAwareRiskManager) and atr and atr > 0:
                stop_price, take_price = risk_manager.regime_stop.atr_based_for_regime(
                    entry_price, "buy", atr, regime
                )
                size = risk_manager.regime_sizer.size_for_regime(
                    self.equity, entry_price, stop_price, atr=atr, regime=regime
                )
            else:
                if atr and atr > 0:
                    stop_price = risk_manager.stop.atr_based(
                        entry_price, "buy", atr, multiplier=2.0
                    )
                else:
                    stop_price = entry_price * 0.95
                size = risk_manager.sizer.size(
                    self.equity, entry_price, stop_price, atr=atr
                )

            if size <= 0:
                return
            pos = {
                "symbol": signal.symbol,
                "side": "long",
                "entry_price": entry_price,
                "size": size,
                "stop": stop_price,
                "entry_time": signal.timestamp,
                "peak_price": entry_price,
            }
            if isinstance(risk_manager, RegimeAwareRiskManager):
                pos["trailing_active"] = False
            self.positions.append(pos)
            self.capital -= size * entry_price * (1 + self.commission)

        elif signal.side == "sell":
            # Close existing long
            for pos in list(self.positions):
                if pos["symbol"] == signal.symbol and pos["side"] == "long":
                    exit_price = bar["close"] * (1 - self.slippage)
                    pnl = (exit_price - pos["entry_price"]) * pos["size"]
                    pnl -= pos["size"] * exit_price * self.commission
                    self.capital += pos["size"] * exit_price * (1 - self.commission)
                    self.trades.append(
                        Trade(
                            entry_time=pos["entry_time"],
                            exit_time=signal.timestamp,
                            symbol=pos["symbol"],
                            side="long",
                            entry_price=pos["entry_price"],
                            exit_price=exit_price,
                            size=pos["size"],
                            pnl=pnl,
                            exit_reason="signal",
                        )
                    )
                    self.positions.remove(pos)

    def _check_stops(self, bar: pd.Series, risk_manager: RiskManager):
        """Check stop-loss and trailing stops for all open positions."""
        for pos in list(self.positions):
            if pos["side"] == "long":
                # Fixed stop hit
                stop = pos.get("stop", 0)
                if stop > 0 and bar["low"] <= stop:
                    exit_price = bar["open"] if bar["open"] <= stop else stop
                    self._close_position(pos, bar, exit_price, "stop_loss")
                    continue

                # Trailing stop (only if RegimeAwareRiskManager)
                if isinstance(risk_manager, RegimeAwareRiskManager):
                    triggered = risk_manager.trailing.update(pos, bar)
                    if triggered:
                        exit_price = (
                            bar["open"] if bar["open"] <= pos["stop"] else pos["stop"]
                        )
                        self._close_position(pos, bar, exit_price, "trailing_stop")

    def _close_position(
        self, pos: dict, bar: pd.Series, exit_price: float, reason: str
    ):
        """Close a single position and record the trade."""
        pnl = (exit_price - pos["entry_price"]) * pos["size"]
        pnl -= pos["size"] * exit_price * self.commission
        self.capital += pos["size"] * exit_price * (1 - self.commission)
        self.trades.append(
            Trade(
                entry_time=pos["entry_time"],
                exit_time=bar.name,
                symbol=pos["symbol"],
                side=pos["side"],
                entry_price=pos["entry_price"],
                exit_price=exit_price,
                size=pos["size"],
                pnl=pnl,
                exit_reason=reason,
            )
        )
        self.positions.remove(pos)

    def _update_equity(self, bar: pd.Series):
        position_value = 0.0
        for pos in self.positions:
            mtm_price = bar["close"]
            position_value += mtm_price * pos["size"]
        self.equity = self.capital + position_value

    def _build_result(self) -> BacktestResult:
        eq = (
            pd.DataFrame(self.equity_history).set_index("timestamp")["equity"]
            if self.equity_history
            else pd.Series([self.initial_capital])
        )
        returns = eq.pct_change().dropna()

        total_return = (eq.iloc[-1] / self.initial_capital) - 1 if len(eq) > 0 else 0
        sharpe = (
            returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        )

        peak = eq.expanding().max()
        drawdown = (eq - peak) / peak
        max_dd = drawdown.min()

        wins = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl <= 0]
        winrate = len(wins) / len(self.trades) if self.trades else 0
        profit_factor = (
            sum(wins) / abs(sum(losses))
            if losses and sum(losses) != 0
            else float("inf")
        )

        # Estimate total transaction cost (commission + slippage) per round-trip
        total_cost = 0.0
        for t in self.trades:
            entry_commission = t.size * t.entry_price * self.commission
            exit_commission = t.size * t.exit_price * self.commission
            entry_slippage = (
                t.size * t.entry_price * self.slippage / (1 + self.slippage)
            )
            exit_slippage = t.size * t.exit_price * self.slippage / (1 - self.slippage)
            total_cost += (
                entry_commission + exit_commission + entry_slippage + exit_slippage
            )

        return BacktestResult(
            equity_curve=eq,
            trades=self.trades,
            total_return=total_return,
            sharpe=sharpe,
            max_drawdown=max_dd,
            winrate=winrate,
            profit_factor=profit_factor,
            total_cost=total_cost,
        )
