"""Live trading wrapper with safety gates and production safeguards.

Graduation Gate (paper → live):
    - Paper trading 30 days profitable
    - Max drawdown < 10%
    - Sharpe > 0.5
    - Winrate > 40% and profit factor > 1.2

Safety Rules:
    - Max 1% risk per trade
    - Max 10% total exposure
    - Max 15% drawdown → halt
    - Orders validated before submission
    - All trades logged to journal + Telegram alerted
"""

import argparse
import os
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd
from loguru import logger

from data.feed import DataFeed
from execution.connectors.ccxt_connector import CCXTConnector
from execution.order_manager import OrderManager, OrderSide, OrderType
from risk.manager import RiskManager
from risk.psychology import PsychologicalEnforcer
from journal.trade_logger import TradeLogger, TradeRecord, EquitySnapshot
from monitoring.telegram import TelegramAlerter
from monitoring.health_server import HealthServer
from strategies.base import BaseStrategy, StrategyContext
from ml.drift_detection import ModelDriftMonitor


class GraduationGate:
    """Safety gate: only allow live trading if paper metrics pass thresholds."""

    THRESHOLDS = {
        "min_paper_days": 30,
        "max_drawdown": 0.10,
        "min_sharpe": 0.5,
        "min_winrate": 0.40,
        "min_profit_factor": 1.2,
    }

    @classmethod
    def evaluate(cls, journal: TradeLogger) -> Dict:
        """Evaluate paper trading history from journal."""
        summary = journal.trade_summary()
        if summary.get("count", 0) < 5:
            return {"passed": False, "reason": "Insufficient paper trades (< 5)"}

        # Check date range
        trades = journal.get_trades(limit=10000)
        if trades:
            first_trade = min(t.timestamp for t in trades)
            paper_days = (datetime.now() - first_trade).days
            if paper_days < cls.THRESHOLDS["min_paper_days"]:
                return {
                    "passed": False,
                    "reason": f"Paper trading only {paper_days} days (need {cls.THRESHOLDS['min_paper_days']})",
                }

        # Check metrics
        reasons = []
        # We don't have Sharpe in trade_summary yet, approximate from snapshots
        snapshots = journal.get_snapshots(limit=1000)
        if snapshots:
            equity_series = pd.Series([s.equity for s in reversed(snapshots)])
            returns = equity_series.pct_change().dropna()
            if len(returns) > 1:
                sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0
                if sharpe < cls.THRESHOLDS["min_sharpe"]:
                    reasons.append(f"Sharpe {sharpe:.2f} < {cls.THRESHOLDS['min_sharpe']}")

        winrate = summary.get("winrate", 0)
        if winrate < cls.THRESHOLDS["min_winrate"]:
            reasons.append(f"Winrate {winrate:.1%} < {cls.THRESHOLDS['min_winrate']:.1%}")

        pf = summary.get("profit_factor", float("inf"))
        if pf < cls.THRESHOLDS["min_profit_factor"]:
            reasons.append(f"Profit factor {pf:.2f} < {cls.THRESHOLDS['min_profit_factor']}")

        # Check max drawdown from snapshots
        if snapshots:
            peak = 0
            max_dd = 0
            for s in reversed(snapshots):
                if s.equity > peak:
                    peak = s.equity
                dd = (peak - s.equity) / peak if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd
            if max_dd > cls.THRESHOLDS["max_drawdown"]:
                reasons.append(f"Max drawdown {max_dd:.1%} > {cls.THRESHOLDS['max_drawdown']:.1%}")

        if reasons:
            return {"passed": False, "reason": "; ".join(reasons)}

        return {"passed": True, "reason": "All gates passed"}


class LiveTradingEngine:
    """Production trading engine with full safety stack.

    Architecture:
        Data Feed → Strategy → Risk Manager → Order Manager → Exchange
                                        ↓
                                    Journal + Telegram
    """

    def __init__(
        self,
        config: dict,
        strategy: BaseStrategy,
        mode: str = "paper",
        symbols: Optional[List[str]] = None,
    ):
        self.config = config
        self.strategy = strategy
        self.mode = mode  # "paper" or "live"
        self.symbols = symbols or config.get("data", {}).get("symbols", ["BTC/USDT"])
        self.timeframe = config.get("data", {}).get("timeframe", "1d")

        # Risk
        risk_cfg = config.get("risk", {})
        self.risk = RiskManager(risk_cfg)

        # Psychology enforcer
        psych_cfg = config.get("psychology", {})
        self.psych_enforcer = PsychologicalEnforcer(psych_cfg)

        # Execution
        exec_cfg = config.get("execution", {})
        self.paper_mode = mode == "paper" or exec_cfg.get("paper", True)

        if self.paper_mode:
            self.connector = None
            logger.info("Running in PAPER mode")
        else:
            self.connector = CCXTConnector(
                exchange_id=exec_cfg.get("exchange_id", "binance"),
                api_key=exec_cfg.get("api_key", ""),
                api_secret=exec_cfg.get("api_secret", ""),
                testnet=exec_cfg.get("testnet", True),
            )
            logger.info("Running in LIVE mode")

        self.order_manager = OrderManager(
            connector=self.connector,
            paper_mode=self.paper_mode,
        )

        # Data
        self.feed = DataFeed()

        # Journal
        db_path = config.get("journal", {}).get("db_path", "./data/journal.db")
        self.journal = TradeLogger(db_path=db_path)

        # Alerts
        alert_cfg = config.get("monitoring", {})
        self.alerter = TelegramAlerter(
            enabled=alert_cfg.get("alert_telegram", False),
        )

        # Drift monitor (for ML strategies)
        drift_cfg = config.get("drift", {})
        self.drift_monitor = ModelDriftMonitor(
            confidence_window=drift_cfg.get("confidence_window", 30),
            psi_threshold=drift_cfg.get("psi_threshold", 0.2),
            error_threshold=drift_cfg.get("error_threshold", 0.55),
            drift_cooldown_days=drift_cfg.get("cooldown_days", 7),
        ) if drift_cfg.get("enabled", False) else None

        # Health server
        health_port = config.get("monitoring", {}).get("health_port", 8080)
        self.health_server = HealthServer(
            port=health_port,
            status_provider=self.get_status,
        )

        # State
        self.capital = config.get("backtest", {}).get("initial_capital", 100000.0)
        self.equity = self.capital
        self.positions: Dict[str, dict] = {}
        self.is_running = False
        self.last_bar_times: Dict[str, datetime] = {}
        self.check_interval = 60  # seconds

    def run(self):
        """Main trading loop."""
        # Safety gate for live mode
        if not self.paper_mode:
            gate = GraduationGate.evaluate(self.journal)
            if not gate["passed"]:
                logger.error(f"LIVE GATE BLOCKED: {gate['reason']}")
                self.alerter.send_error(
                    f"Live trading blocked: {gate['reason']}",
                    context="GraduationGate",
                )
                raise RuntimeError(f"Cannot start live trading: {gate['reason']}")
            logger.info("✅ Graduation gate passed — starting live trading")

        self.is_running = True
        self.health_server.start()
        self.alerter.send_startup(
            mode=self.mode,
            symbols=self.symbols,
            strategies=[self.strategy.__class__.__name__],
        )

        logger.info(f"Trading loop started | Symbols: {self.symbols} | TF: {self.timeframe}")

        iteration = 0
        while self.is_running:
            try:
                for symbol in self.symbols:
                    self._process_symbol(symbol)

                # Periodic equity snapshot
                if iteration % 10 == 0:
                    self._snapshot()

                # Periodic drift check (every 50 iterations ≈ 50 minutes)
                if iteration % 50 == 0 and self.drift_monitor is not None:
                    self._check_drift()

                # Daily summary at midnight UTC
                if datetime.now().hour == 0 and datetime.now().minute < 2:
                    self._send_daily_summary()

            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                self.alerter.send_error(str(e), context="TradingLoop")

            iteration += 1
            time.sleep(self.check_interval)

        logger.info("Trading loop stopped")

    def _process_symbol(self, symbol: str):
        """Process one symbol: fetch data, generate signal, execute."""
        df = self.feed.fetch(symbol, timeframe=self.timeframe, limit=200, use_cache=False)
        if df.empty or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return

        latest_bar = df.iloc[-1]
        latest_time = df.index[-1]

        # Skip if bar hasn't updated
        if self.last_bar_times.get(symbol) == latest_time:
            return
        self.last_bar_times[symbol] = latest_time

        # Warmup
        if not self.strategy.is_warm:
            self.strategy.warmup(df.iloc[:100])
            if not self.strategy.is_warm:
                return

        # Risk check
        status = self.risk.check(self.capital, self.equity, list(self.positions.values()))
        if status["halted"]:
            logger.error(f"DRAWDOWN HALT | Equity: ${self.equity:,.2f}")
            self.alerter.send_drawdown_alert(
                current_drawdown=status["drawdown"] or 0,
                max_allowed=self.risk.guard.max_drawdown_pct,
                equity=self.equity,
                peak=self.risk.guard.peak,
            )
            self.stop()
            return

        # Build context
        context = StrategyContext(
            symbol=symbol,
            bar=latest_bar,
            history=df,
            account={"capital": self.capital, "equity": self.equity},
            positions=list(self.positions.values()),
        )

        # Get signal
        signal = self.strategy.on_bar(context)
        if not signal:
            return

        # Psychological check
        psych_state = self.psych_enforcer.check_state()
        if psych_state.is_paused:
            logger.warning(
                f"🧠 PSYCH BLOCK: {psych_state.blocked_reason}"
            )
            return

        # Validate exposure
        if not status["exposure_ok"]:
            logger.warning(f"Max exposure reached. Ignoring {signal.side} signal on {symbol}")
            return

        # Execute (psychological size multiplier applied inside)
        self._execute_signal(symbol, signal, latest_bar, psych_state)
        self._update_equity(symbol, latest_bar)

    def _execute_signal(self, symbol: str, signal, bar, psych_state=None):
        """Convert strategy signal to order and submit."""
        price = bar["close"]
        psych_multiplier = psych_state.size_multiplier if psych_state else 1.0

        if signal.side == "buy":
            # Calculate position size
            atr = signal.meta.get("atr") if signal.meta else None
            if atr and atr > 0:
                stop = self.risk.stop.atr_based(price, "buy", atr, 2.0)
            else:
                stop = price * 0.95
            size = self.risk.sizer.size(self.equity, price, stop, atr=atr)
            if size <= 0:
                return

            # Apply psychological size multiplier
            if psych_multiplier < 1.0:
                original_size = size
                size *= psych_multiplier
                logger.info(
                    f"🧠 Size adjusted: {original_size:.6f} → {size:.6f} "
                    f"({psych_multiplier:.0%} due to psychology)"
                )

            # Create and submit order
            order = self.order_manager.create_order(
                symbol=symbol,
                side=OrderSide.BUY,
                amount=size,
                order_type=OrderType.MARKET,
                strategy_name=self.strategy.__class__.__name__,
                reason=getattr(signal, 'reason', '') or "signal",
            )
            result = self.order_manager.submit(order, last_price=price)

            if result.success:
                self.positions[symbol] = {
                    "symbol": symbol,
                    "side": "long",
                    "entry_price": price,
                    "size": size,
                    "stop": stop,
                    "entry_time": signal.timestamp,
                }
                self.capital -= size * price * 1.001
                self.alerter.send_signal(
                    symbol=symbol,
                    side="buy",
                    price=price,
                    size=size,
                    strategy=self.strategy.__class__.__name__,
                    reason=getattr(signal, 'reason', '') or "",
                )
                logger.info(f"BUY {symbol} @ {price:.2f} | Size: {size:.6f}")

        elif signal.side == "sell":
            pos = self.positions.get(symbol)
            if not pos or pos["side"] != "long":
                return

            order = self.order_manager.create_order(
                symbol=symbol,
                side=OrderSide.SELL,
                amount=pos["size"],
                order_type=OrderType.MARKET,
                strategy_name=self.strategy.__class__.__name__,
                reason=getattr(signal, 'reason', '') or "signal",
            )
            result = self.order_manager.submit(order, last_price=price)

            if result.success:
                pnl = (price - pos["entry_price"]) * pos["size"]
                pnl_pct = (price - pos["entry_price"]) / pos["entry_price"]
                self.capital += pos["size"] * price * 0.999

                # Log trade
                self.journal.log_trade(TradeRecord(
                    symbol=symbol,
                    strategy=self.strategy.__class__.__name__,
                    side="long",
                    entry_price=pos["entry_price"],
                    exit_price=price,
                    size=pos["size"],
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason="signal",
                    reasoning=getattr(signal, 'reason', '') or "",
                ))

                # Update psychological state with P&L
                emotion = signal.meta.get("emotion") if signal.meta else None
                self.psych_enforcer.check_state(pnl=pnl, emotion=emotion)

                self.alerter.send_trade_closed(
                    symbol=symbol,
                    side="long",
                    entry=pos["entry_price"],
                    exit_price=price,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason="signal",
                )

                del self.positions[symbol]
                logger.info(f"SELL {symbol} @ {price:.2f} | P&L: ${pnl:.2f}")

    def _update_equity(self, symbol: str, bar):
        """Recalculate total equity."""
        position_value = sum(
            p["size"] * bar["close"] for p in self.positions.values()
        )
        self.equity = self.capital + position_value

    def _snapshot(self):
        """Record equity snapshot to journal."""
        exposure = sum(
            p.get("size", 0) * p.get("entry_price", 0)
            for p in self.positions.values()
        )
        peak = self.risk.guard.peak or self.equity
        dd = (peak - self.equity) / peak if peak > 0 else 0

        self.journal.snapshot(EquitySnapshot(
            equity=self.equity,
            cash=self.capital,
            open_positions=len(self.positions),
            open_exposure=exposure,
            drawdown_pct=dd,
            daily_pnl=0,  # calculated separately
        ))

    def _send_daily_summary(self):
        """Send daily P&L summary via Telegram."""
        today = datetime.now().strftime("%Y-%m-%d")
        trades = self.journal.get_trades(start=f"{today}T00:00:00")
        pnl = sum(t.pnl for t in trades)
        wins = [t for t in trades if t.pnl > 0]
        winrate = len(wins) / len(trades) if trades else 0

        self.alerter.send_daily_summary(
            trades_today=len(trades),
            pnl_today=pnl,
            winrate_today=winrate,
            equity=self.equity,
            open_positions=len(self.positions),
        )

    def stop(self):
        self.is_running = False
        self.health_server.stop()

    def _check_drift(self):
        """Check model drift and alert if detected."""
        if self.drift_monitor is None:
            return
        report = self.drift_monitor.check()
        if report.is_drifted:
            logger.warning(
                f"🚨 MODEL DRIFT DETECTED | Score: {report.overall_drift_score:.3f} | "
                f"{report.recommendation}"
            )
            self.alerter.send_error(
                f"Model drift detected (score={report.overall_drift_score:.3f}). {report.recommendation}",
                context="ModelDrift",
            )
            # Save drift report
            self.drift_monitor.save("./data/drift_history.json")

    def get_status(self) -> dict:
        """Return current engine status (for health check / monitoring)."""
        status = {
            "mode": self.mode,
            "running": self.is_running,
            "equity": self.equity,
            "capital": self.capital,
            "open_positions": len(self.positions),
            "symbols": self.symbols,
            "strategy": self.strategy.__class__.__name__,
            "paper_mode": self.paper_mode,
            "timestamp": datetime.now().isoformat(),
        }
        # Add psychological state
        psych = self.psych_enforcer.get_summary()
        status["psychology"] = psych
        # Add drift summary
        if self.drift_monitor:
            status["drift"] = self.drift_monitor.get_summary()
        return status


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Live Trading Engine")
    parser.add_argument("--config", default="config/system.yaml")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--strategy", default="RegimeEnsemble", choices=["RegimeEnsemble", "EMA-Trend"])
    args = parser.parse_args()

    config = load_config(args.config)

    # Override mode from CLI
    config["system"]["mode"] = args.mode

    # Import strategy dynamically
    if args.strategy == "RegimeEnsemble":
        from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy
        strategy = RegimeEnsembleStrategy(params=config["strategies"]["registry"][2]["params"])
    else:
        from strategies.rule_based.ema_trend import EMATrendStrategy
        strategy = EMATrendStrategy()

    engine = LiveTradingEngine(
        config=config,
        strategy=strategy,
        mode=args.mode,
        symbols=[args.symbol],
    )

    try:
        engine.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        engine.stop()


if __name__ == "__main__":
    main()
