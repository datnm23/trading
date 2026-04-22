"""Paper trading engine that simulates live execution."""

import time
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

import pandas as pd
from loguru import logger

from data.feed import DataFeed
from strategies.base import BaseStrategy
from risk.manager import RiskManager, RegimeAwareRiskManager


@dataclass
class PaperTrade:
    timestamp: datetime
    symbol: str
    side: str
    price: float
    size: float
    pnl: float = 0.0
    reason: str = ""


class PaperTradingEngine:
    """Simulates live trading by fetching latest bar and executing signals."""

    def __init__(
        self,
        strategy: BaseStrategy,
        risk_manager: RiskManager,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        initial_capital: float = 100000.0,
        check_interval_seconds: int = 60,
    ):
        self.strategy = strategy
        self.risk = risk_manager
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.equity = initial_capital
        self.check_interval = check_interval_seconds

        self.feed = DataFeed()
        self.positions = []
        self.trades = []
        self.is_running = False
        self.last_bar_time = None
        self._is_regime_aware = isinstance(risk_manager, RegimeAwareRiskManager)

    def run_once(self) -> Optional[dict]:
        """Execute one trading cycle. Returns trade info if any."""
        # Fetch latest data
        df = self.feed.fetch(self.symbol, timeframe=self.timeframe, limit=200, use_cache=True)
        if df.empty or len(df) < 50:
            logger.warning("Insufficient data")
            return None

        latest_bar = df.iloc[-1]
        latest_time = df.index[-1]

        # Skip if bar hasn't updated
        if self.last_bar_time == latest_time:
            return None
        self.last_bar_time = latest_time

        # Warmup strategy on first run
        if not self.strategy.is_warm:
            self.strategy.warmup(df.iloc[:100])
            if not self.strategy.is_warm:
                return None

        # Build context
        from strategies.base import StrategyContext
        context = StrategyContext(
            symbol=self.symbol,
            bar=latest_bar,
            history=df,
            account={"capital": self.capital, "equity": self.equity},
            positions=self.positions,
        )

        # Risk check
        status = self.risk.check(self.capital, self.equity, self.positions)
        if status["halted"]:
            logger.warning("Drawdown guard triggered. Stopping.")
            self.stop()
            return None

        # Get signal
        signal = self.strategy.on_bar(context)
        if not signal:
            return None

        # Execute signal
        result = self._execute(signal, latest_bar)
        self._update_equity(latest_bar)

        logger.info(
            f"Paper trade | {signal.side.upper()} {self.symbol} @ {latest_bar['close']:.2f} | "
            f"Equity: ${self.equity:,.2f} | Positions: {len(self.positions)}"
        )
        return result

    def _execute(self, signal, bar) -> dict:
        price = bar["close"]
        regime = signal.meta.get("directional_regime", "neutral") if signal.meta else "neutral"

        if self._is_regime_aware:
            self.risk.set_regime(regime)

        if signal.side == "buy":
            # Calculate position size
            atr = signal.meta.get("atr") if signal.meta else None

            if self._is_regime_aware and atr and atr > 0:
                stop_price = self.risk.regime_stop.atr_based_for_regime(price, "buy", atr, regime)[0]
                size = self.risk.regime_sizer.size_for_regime(self.equity, price, stop_price, atr=atr, regime=regime)
            elif atr and atr > 0:
                stop_price = self.risk.stop.atr_based(price, "buy", atr, 2.0)
                size = self.risk.sizer.size(self.equity, price, stop_price, atr=atr)
            else:
                stop_price = price * 0.95
                size = self.risk.sizer.size(self.equity, price, stop_price)

            if size <= 0:
                return {}

            self.positions.append({
                "symbol": self.symbol,
                "side": "long",
                "entry_price": price,
                "size": size,
                "stop": stop_price,
                "entry_time": signal.timestamp,
            })
            self.capital -= size * price * 1.001  # include commission
            return {"side": "buy", "price": price, "size": size}

        elif signal.side == "sell":
            for pos in list(self.positions):
                if pos["symbol"] == self.symbol and pos["side"] == "long":
                    pnl = (price - pos["entry_price"]) * pos["size"]
                    self.capital += pos["size"] * price * 0.999
                    self.trades.append(PaperTrade(
                        timestamp=signal.timestamp,
                        symbol=self.symbol,
                        side="sell",
                        price=price,
                        size=pos["size"],
                        pnl=pnl,
                        reason="signal",
                    ))
                    self.positions.remove(pos)
                    return {"side": "sell", "price": price, "size": pos["size"], "pnl": pnl}
            return {}

        return {}

    def _update_equity(self, bar):
        position_value = sum(p["size"] * bar["close"] for p in self.positions)
        self.equity = self.capital + position_value

    def run(self, max_iterations: Optional[int] = None):
        """Run paper trading loop."""
        self.is_running = True
        iteration = 0
        logger.info(f"Starting paper trading | Symbol: {self.symbol} | Capital: ${self.initial_capital:,.2f}")

        while self.is_running:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")

            iteration += 1
            if max_iterations and iteration >= max_iterations:
                break

            time.sleep(self.check_interval)

        logger.info("Paper trading stopped.")

    def stop(self):
        self.is_running = False

    def get_summary(self) -> dict:
        """Get current trading summary."""
        total_pnl = sum(t.pnl for t in self.trades)
        wins = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl <= 0]
        return {
            "capital": self.capital,
            "equity": self.equity,
            "total_return": (self.equity / self.initial_capital) - 1,
            "open_positions": len(self.positions),
            "total_trades": len(self.trades),
            "winrate": len(wins) / len(self.trades) if self.trades else 0,
            "profit_factor": sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float("inf"),
            "total_pnl": total_pnl,
        }
