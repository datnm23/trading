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
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from loguru import logger

# Load .env for Telegram tokens, DB URLs, etc.
_dotenv_path = Path(__file__).parent.parent / ".env"
if _dotenv_path.exists():
    load_dotenv(_dotenv_path)

from data.feed import DataFeed
from execution.connectors.ccxt_connector import CCXTConnector
from execution.order_manager import OrderManager, OrderSide, OrderType
from execution.order_retry import OrderRetryManager, RetryConfig
from execution.partial_exit import PartialExitManager
from execution.slippage_tracker import SlippageTracker
from execution.trailing_stop import TrailingStopConfig, TrailingStopManager
from journal.trade_logger import EquitySnapshot, TradeLogger, TradeRecord
from ml.drift_detection import ModelDriftMonitor
from monitoring.daily_report import DailyReportGenerator
from monitoring.drawdown_alerts import DrawdownAlertManager
from monitoring.health_server import HealthServer
from monitoring.price_alerts import PriceAlertManager
from monitoring.telegram import TelegramAlerter
from monitoring.volume_alerts import VolumeAlertManager
from risk.correlation_guard import CorrelationGuard
from risk.manager import RegimeAwareRiskManager, RiskManager
from risk.psychology import PsychologicalEnforcer
from strategies.base import BaseStrategy, StrategyContext


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
    def evaluate(cls, journal: TradeLogger) -> dict:
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
                sharpe = (
                    (returns.mean() / returns.std()) * (252**0.5)
                    if returns.std() > 0
                    else 0
                )
                if sharpe < cls.THRESHOLDS["min_sharpe"]:
                    reasons.append(
                        f"Sharpe {sharpe:.2f} < {cls.THRESHOLDS['min_sharpe']}"
                    )

        winrate = summary.get("winrate", 0)
        if winrate < cls.THRESHOLDS["min_winrate"]:
            reasons.append(
                f"Winrate {winrate:.1%} < {cls.THRESHOLDS['min_winrate']:.1%}"
            )

        pf = summary.get("profit_factor", float("inf"))
        if pf < cls.THRESHOLDS["min_profit_factor"]:
            reasons.append(
                f"Profit factor {pf:.2f} < {cls.THRESHOLDS['min_profit_factor']}"
            )

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
                reasons.append(
                    f"Max drawdown {max_dd:.1%} > {cls.THRESHOLDS['max_drawdown']:.1%}"
                )

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
        symbols: list[str] | None = None,
    ):
        self.config = config
        self.strategy = strategy
        self.mode = mode  # "paper" or "live"
        self.symbols = symbols or config.get("data", {}).get("symbols", ["BTC/USDT"])
        self.timeframe = config.get("data", {}).get("timeframe", "1d")

        # Risk
        risk_cfg = config.get("risk", {})
        # Use RegimeAwareRiskManager for regime-based strategies
        if strategy.__class__.__name__ in ("RegimeEnsembleStrategy", "RegimeEnsemble"):
            self.risk = RegimeAwareRiskManager(risk_cfg)
        else:
            self.risk = RiskManager(risk_cfg)

        # Psychology enforcer
        psych_cfg = config.get("psychology", {})
        self.psych_enforcer = PsychologicalEnforcer(psych_cfg)

        # Execution
        exec_cfg = config.get("execution", {})
        self.paper_mode = mode == "paper" or exec_cfg.get("paper", True)

        # Always create a connector for real-time price fetching (even in paper mode)
        self.connector = CCXTConnector(
            exchange_id=exec_cfg.get("exchange_id", "binance"),
            api_key=exec_cfg.get("api_key", ""),
            api_secret=exec_cfg.get("api_secret", ""),
            testnet=exec_cfg.get("testnet", True),
        )
        if self.paper_mode:
            logger.info("Running in PAPER mode (real-time price feed active)")
        else:
            logger.info("Running in LIVE mode")

        self.order_manager = OrderManager(
            connector=self.connector,
            paper_mode=self.paper_mode,
        )

        # Data
        self.feed = DataFeed()

        # Journal (PostgreSQL only)
        journal_cfg = config.get("journal", {})
        db_url = os.environ.get("TRADING_DB_URL") or journal_cfg.get("db_url")
        if not db_url:
            raise ValueError("journal.db_url is required in config (PostgreSQL only)")
        self.journal = TradeLogger(db_url=db_url)

        # Alerts
        alert_cfg = config.get("monitoring", {})
        self.alerter = TelegramAlerter(
            enabled=alert_cfg.get("alert_telegram", False),
        )

        # Price alerts (bilingual EN/VN, real-time via connector)
        price_alert_cfg = config.get("price_alerts", {})
        self.price_alerter = PriceAlertManager(
            alerter=self.alerter,
            connector=self.connector,
            enabled=price_alert_cfg.get("enabled", True),
            threshold_pct=price_alert_cfg.get("threshold_pct", 0.008),
        )

        # Drawdown alerts (warning before circuit breaker)
        dd_alert_cfg = config.get("drawdown_alerts", {})
        self.drawdown_alerter = DrawdownAlertManager(
            alerter=self.alerter,
            enabled=dd_alert_cfg.get("enabled", True),
            warning_pct=dd_alert_cfg.get("warning_pct", 0.10),
            cooldown_hours=dd_alert_cfg.get("cooldown_hours", 4.0),
        )

        # Volume spike alerts
        vol_alert_cfg = config.get("volume_alerts", {})
        self.volume_alerter = VolumeAlertManager(
            alerter=self.alerter,
            enabled=vol_alert_cfg.get("enabled", True),
            lookback_bars=vol_alert_cfg.get("lookback_bars", 20),
            multiplier=vol_alert_cfg.get("multiplier", 2.5),
            cooldown_hours=vol_alert_cfg.get("cooldown_hours", 4.0),
        )

        # Drift monitor (for ML strategies)
        drift_cfg = config.get("drift", {})
        self.drift_monitor = (
            ModelDriftMonitor(
                confidence_window=drift_cfg.get("confidence_window", 30),
                psi_threshold=drift_cfg.get("psi_threshold", 0.2),
                error_threshold=drift_cfg.get("error_threshold", 0.55),
                drift_cooldown_days=drift_cfg.get("cooldown_days", 7),
            )
            if drift_cfg.get("enabled", False)
            else None
        )

        # New: Trailing Stop Manager
        trail_cfg = config.get("risk", {})
        self.trailing_stop = TrailingStopManager(
            TrailingStopConfig(
                activation_pct=trail_cfg.get("trailing_activation", 0.05),
                trail_pct=trail_cfg.get("trailing_trail_pct", 0.30),
                min_profit_lock=trail_cfg.get("trailing_min_profit", 0.02),
            )
        )

        # New: Partial Exit Manager
        self.partial_exit = PartialExitManager()

        # New: Correlation Guard
        self.correlation_guard = CorrelationGuard(
            max_correlation=trail_cfg.get("max_correlation", 0.80),
            lookback_days=trail_cfg.get("correlation_lookback", 90),
        )

        # New: Order Retry Manager
        self.order_retry = OrderRetryManager(
            RetryConfig(
                max_retries=exec_cfg.get("max_retries", 3),
                base_delay=exec_cfg.get("retry_base_delay", 1.0),
                max_delay=exec_cfg.get("retry_max_delay", 30.0),
            )
        )

        # New: Slippage Tracker
        self.slippage_tracker = SlippageTracker(
            warning_threshold_pct=exec_cfg.get("slippage_warning_pct", 0.001)
        )

        # New: Daily Report Generator
        self.daily_report = DailyReportGenerator(
            db_url=journal_cfg.get("db_url"),
        )

        # Health server
        health_port = config.get("monitoring", {}).get("health_port", 8080)
        self.health_server = HealthServer(
            port=health_port,
            status_provider=self.get_status,
        )

        # State
        self.capital = config.get("backtest", {}).get("initial_capital", 100000.0)
        self.equity = self.capital
        self.positions: dict[str, dict] = {}
        self.is_running = False
        self.last_bar_times: dict[str, datetime] = {}
        self.check_interval = 60  # seconds
        self._was_psych_paused = False  # Track pause→resume transitions
        self._last_daily_summary_date = None  # Track daily summary to avoid duplicates
        self._lock = threading.Lock()  # Protect shared mutable state

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

        logger.info(
            f"Trading loop started | Symbols: {self.symbols} | TF: {self.timeframe}"
        )

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

                # Daily summary at midnight UTC (once per day)
                today = datetime.now().date()
                if (
                    datetime.now().hour == 0
                    and datetime.now().minute < 2
                    and today != self._last_daily_summary_date
                ):
                    self._send_daily_summary()
                    self._last_daily_summary_date = today

            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                self.alerter.send_error(str(e), context="TradingLoop")

            iteration += 1
            time.sleep(self.check_interval)

        logger.info("Trading loop stopped")

    def _process_symbol(self, symbol: str):
        """Process one symbol: fetch data, generate signal, execute."""
        df = self.feed.fetch(
            symbol, timeframe=self.timeframe, limit=200, use_cache=True
        )
        if df.empty or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return

        latest_bar = df.iloc[-1]
        latest_time = df.index[-1]
        current_price = latest_bar["close"]

        # Check price alerts (every iteration, not just new bars)
        self.price_alerter.check(symbol, current_price)

        # Skip if bar hasn't updated
        if self.last_bar_times.get(symbol) == latest_time:
            return
        self.last_bar_times[symbol] = latest_time

        # Check volume spike on new bar
        self.volume_alerter.check(symbol, df)

        # Update correlation guard with latest data
        self.correlation_guard.update_data(symbol, df)

        # Check trailing stop for existing positions
        if symbol in self.positions:
            self.trailing_stop.update(symbol, current_price)
            if self.trailing_stop.should_exit(symbol, current_price):
                stop_level = self.trailing_stop.get_stop(symbol)
                logger.info(
                    f"🛑 TRAILING STOP HIT for {symbol} at {current_price:.2f} (stop: {stop_level:.2f})"
                )
                from strategies.base import Signal

                trailing_signal = Signal(
                    timestamp=latest_time,
                    symbol=symbol,
                    side="sell",
                    strength=1.0,
                    meta={"reason": "trailing_stop"},
                )
                self._execute_signal(symbol, trailing_signal, latest_bar)
                self.trailing_stop.remove_position(symbol)
                self.partial_exit.remove_position(symbol)
                return

            # Check partial exit (scale-out)
            exits = self.partial_exit.check(symbol, current_price)
            for exit_info in exits:
                self._execute_partial_exit(symbol, exit_info, latest_bar)

        # Warmup
        if not self.strategy.is_warm:
            self.strategy.warmup(df.iloc[:100])
            if not self.strategy.is_warm:
                return

        # Drawdown warning (before circuit breaker)
        self.drawdown_alerter.check(self.equity)

        # Risk check
        status = self.risk.check(
            self.capital, self.equity, list(self.positions.values())
        )
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
            reasons = []
            if hasattr(self.strategy, "last_status") and self.strategy.last_status:
                reasons = self.strategy.last_status.get("rejection_reasons", [])
                regime = self.strategy.last_status.get("regime", "?")
                directional = self.strategy.last_status.get("directional_regime", "?")
                logger.info(
                    f"No signal for {symbol} | Regime: {regime}/{directional} | Reasons: {reasons}"
                )
            else:
                logger.debug(
                    f"No signal for {symbol} | Strategy: {self.strategy.__class__.__name__}"
                )
            # Send Telegram alert with reasons why no trade
            if hasattr(self.strategy, "last_status") and self.strategy.last_status:
                status = self.strategy.last_status
                reasons = "\n".join(
                    [f"  • {r}" for r in status.get("rejection_reasons", [])]
                )
                sub_signals = status.get("sub_signals", {})
                sub_text = (
                    ", ".join([f"{k}({v})" for k, v in sub_signals.items()])
                    if sub_signals
                    else "None"
                )
                wiki_align = status.get("wiki_alignment", 0)
                wiki_concepts = status.get("wiki_top_concepts", "")
                wiki_action = status.get("wiki_action", "")
                wiki_min = status.get("wiki_min_alignment", 0.3)
                text = (
                    f"<b>⚪ NO TRADE — {status.get('symbol', symbol)}</b>\n\n"
                    f"Regime: <code>{status.get('regime', '?')}</code> | "
                    f"Directional: <code>{status.get('directional_regime', '?')}</code>\n"
                    f"Sub-signals: <code>{sub_text}</code>\n\n"
                    f"<b>📚 Wiki:</b>\n"
                    f"Action: <code>{wiki_action}</code> | "
                    f"Score: <code>{wiki_align:.2f}</code> (min: <code>{wiki_min:.2f}</code>)\n"
                    f"Concepts: <code>{wiki_concepts[:100]}</code>\n\n"
                    f"<b>Reasons:</b>\n{reasons}\n\n"
                    f"Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
                )
                self.alerter._send(text)
            return

        # Psychological check
        psych_state = self.psych_enforcer.check_state()
        if psych_state.is_paused:
            logger.warning(f"🧠 PSYCH BLOCK: {psych_state.blocked_reason}")
            if not self._was_psych_paused:
                # Send bilingual Telegram alert on NEW pause
                pause_until_str = (
                    psych_state.pause_until.strftime("%Y-%m-%d %H:%M UTC")
                    if psych_state.pause_until
                    else "unknown"
                )
                text = (
                    f"🇺🇸 <b>🧠 BOT PAUSED — Psychology</b>\n\n"
                    f"Reason: <code>{psych_state.blocked_reason}</code>\n"
                    f"Resume: <code>{pause_until_str}</code>\n"
                    f"Daily trades: <code>{psych_state.daily_trades}</code>\n"
                    f"Consecutive losses: <code>{psych_state.consecutive_losses}</code>\n\n"
                    f"🇻🇳 <b>🧠 BOT TẠM DỪNG — Tâm lý</b>\n\n"
                    f"Lý do: <code>{psych_state.blocked_reason}</code>\n"
                    f"Tiếp tục: <code>{pause_until_str}</code>\n"
                    f"Giao dịch hôm nay: <code>{psych_state.daily_trades}</code>\n"
                    f"Thua liên tiếp: <code>{psych_state.consecutive_losses}</code>\n\n"
                    f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
                )
                self.alerter._send(text)
                self._was_psych_paused = True
            return
        else:
            # Was paused before but now resumed (auto-expired or manual)
            if self._was_psych_paused:
                text = (
                    f"🇺🇸 <b>🟢 BOT RESUMED</b>\n\n"
                    f"Psychological pause has expired.\n"
                    f"Trading is now active again.\n\n"
                    f"🇻🇳 <b>🟢 BOT ĐÃ TIẾP TỤC</b>\n\n"
                    f"Tạm dừng tâm lý đã hết hạn.\n"
                    f"Giao dịch đang hoạt động trở lại.\n\n"
                    f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
                )
                self.alerter._send(text)
                self._was_psych_paused = False

        # Daily trade limit alert (not a full pause, but blocks trades)
        if (
            psych_state.blocked_reason
            and "Daily trade limit" in psych_state.blocked_reason
        ):
            logger.warning(f"🧠 PSYCH BLOCK: {psych_state.blocked_reason}")
            text = (
                f"🇺🇸 <b>⚠️ DAILY LIMIT REACHED</b>\n\n"
                f"Trades today: <code>{psych_state.daily_trades}/{self.psych_enforcer.max_daily_trades}</code>\n"
                f"No more trades until tomorrow.\n\n"
                f"🇻🇳 <b>⚠️ ĐÃ ĐẠT GIỚI HẠN NGÀY</b>\n\n"
                f"Giao dịch hôm nay: <code>{psych_state.daily_trades}/{self.psych_enforcer.max_daily_trades}</code>\n"
                f"Không giao dịch thêm đến ngày mai.\n\n"
                f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
            )
            self.alerter._send(text)
            return

        # Validate exposure
        if not status["exposure_ok"]:
            logger.warning(
                f"Max exposure reached. Ignoring {signal.side} signal on {symbol}"
            )
            return

        # Check correlation risk before opening new position
        if signal.side == "buy" and symbol not in self.positions:
            held = [s for s in self.positions.keys()]
            is_safe, corr_reason = self.correlation_guard.check_new_position(
                symbol, held
            )
            if not is_safe:
                logger.warning(f"CORRELATION BLOCK: {corr_reason}")
                self.alerter.send_error(
                    f"Correlation guard blocked {symbol}: {corr_reason}",
                    context="CorrelationGuard",
                )
                return
            logger.info(f"Correlation check passed: {corr_reason}")

        # Execute (psychological size multiplier applied inside)
        self._execute_signal(symbol, signal, latest_bar, psych_state)
        self._update_equity(symbol, latest_bar)

    def _execute_signal(self, symbol: str, signal, bar, psych_state=None):
        """Convert strategy signal to order and submit."""
        with self._lock:
            self._execute_signal_locked(symbol, signal, bar, psych_state)

    def _execute_signal_locked(self, symbol: str, signal, bar, psych_state=None):
        """Internal signal execution under lock."""
        price = bar["close"]
        psych_multiplier = psych_state.size_multiplier if psych_state else 1.0
        regime = (
            signal.meta.get("directional_regime", "neutral")
            if signal.meta
            else "neutral"
        )

        if isinstance(self.risk, RegimeAwareRiskManager):
            self.risk.set_regime(regime)

        if signal.side == "buy":
            # Calculate position size
            atr = signal.meta.get("atr") if signal.meta else None
            if isinstance(self.risk, RegimeAwareRiskManager) and atr and atr > 0:
                stop = self.risk.regime_stop.atr_based_for_regime(
                    price, "buy", atr, regime
                )[0]
                size = self.risk.regime_sizer.size_for_regime(
                    self.equity, price, stop, atr=atr, regime=regime
                )
            elif atr and atr > 0:
                stop = self.risk.stop.atr_based(price, "buy", atr, 2.0)
                size = self.risk.sizer.size(self.equity, price, stop, atr=atr)
            else:
                stop = price * 0.95
                size = self.risk.sizer.size(self.equity, price, stop)
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
                # Alert size reduction
                text = (
                    f"🇺🇸 <b>🧠 SIZE REDUCED — {symbol}</b>\n\n"
                    f"Original: <code>{original_size:.6f}</code>\n"
                    f"Adjusted: <code>{size:.6f}</code>\n"
                    f"Multiplier: <code>{psych_multiplier:.0%}</code>\n"
                    f"Reason: <code>Psychology safeguard</code>\n\n"
                    f"🇻🇳 <b>🧠 GIẢM SIZE — {symbol}</b>\n\n"
                    f"Ban đầu: <code>{original_size:.6f}</code>\n"
                    f"Điều chỉnh: <code>{size:.6f}</code>\n"
                    f"Hệ số: <code>{psych_multiplier:.0%}</code>\n"
                    f"Lý do: <code>Bảo vệ tâm lý</code>\n\n"
                    f"🕐 <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
                )
                self.alerter._send(text)

            # Create and submit order
            order = self.order_manager.create_order(
                symbol=symbol,
                side=OrderSide.BUY,
                amount=size,
                order_type=OrderType.MARKET,
                strategy_name=self.strategy.__class__.__name__,
                reason=getattr(signal, "reason", "") or "signal",
            )
            result = self.order_retry.execute(
                self.order_manager.submit, order, last_price=price
            )

            if result.success:
                self.positions[symbol] = {
                    "symbol": symbol,
                    "side": "long",
                    "entry_price": price,
                    "size": size,
                    "stop": stop,
                    "entry_time": signal.timestamp,
                    "meta": dict(signal.meta) if signal.meta else {},
                }
                self.capital -= size * price * 1.001
                # Wiki detail alert
                wiki_align = signal.meta.get("wiki_alignment", 0) if signal.meta else 0
                wiki_concepts = (
                    signal.meta.get("wiki_top_concepts", "") if signal.meta else ""
                )
                wiki_action = signal.meta.get("wiki_action", "") if signal.meta else ""
                wiki_text = (
                    f"<b>📚 Wiki Validation</b>\n"
                    f"Action: <code>{wiki_action}</code> | "
                    f"Alignment: <code>{wiki_align:.2f}</code>\n"
                    f"Concepts: <code>{wiki_concepts[:120]}</code>"
                )
                self.alerter._send(wiki_text)

                self.alerter.send_signal(
                    symbol=symbol,
                    side="buy",
                    price=price,
                    size=size,
                    strategy=self.strategy.__class__.__name__,
                    reason=getattr(signal, "reason", "") or "",
                )
                logger.info(f"BUY {symbol} @ {price:.2f} | Size: {size:.6f}")

                # Register trailing stop and partial exit for new position
                self.trailing_stop.add_position(symbol, price, stop)
                self.partial_exit.add_position(symbol, price, size)

                # Track slippage (expected vs filled)
                filled_price = getattr(result, "filled_price", price) or price
                self.slippage_tracker.record(symbol, "buy", price, filled_price, size)

                # Log wiki feedback for learning loop
                try:
                    fb_id = self.journal.log_wiki_feedback(
                        {
                            "symbol": symbol,
                            "regime": regime,
                            "side": signal.side,
                            "strategy": self.strategy.__class__.__name__,
                            "wiki_action": wiki_action,
                            "alignment_score": wiki_align,
                            "min_alignment": (
                                signal.meta.get("wiki_min_alignment", 0.3)
                                if signal.meta
                                else 0.3
                            ),
                            "top_concepts": wiki_concepts,
                            "context_summary": (
                                signal.meta.get("wiki_context", "")
                                if signal.meta
                                else ""
                            ),
                        }
                    )
                    # Store feedback ID in position for outcome update on close
                    self.positions[symbol]["wiki_feedback_id"] = fb_id
                except Exception as e:
                    logger.warning(f"Failed to log wiki feedback: {e}")

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
                reason=getattr(signal, "reason", "") or "signal",
            )
            result = self.order_retry.execute(
                self.order_manager.submit, order, last_price=price
            )

            if result.success:
                # Track slippage on exit
                filled_price = getattr(result, "filled_price", price) or price
                self.slippage_tracker.record(
                    symbol, "sell", price, filled_price, pos["size"]
                )

                pnl = (price - pos["entry_price"]) * pos["size"]
                pnl_pct = (price - pos["entry_price"]) / pos["entry_price"]
                self.capital += pos["size"] * price * 0.999

                # Remove from trailing stop / partial exit tracking
                self.trailing_stop.remove_position(symbol)
                self.partial_exit.remove_position(symbol)

                # Log trade with sub-strategy metadata
                trade_meta = dict(pos.get("meta", {}))
                trade_meta["exit_price"] = price
                trade_meta["pnl"] = pnl
                trade_meta["pnl_pct"] = pnl_pct
                trade_meta["exit_reason"] = (
                    getattr(signal, "meta", {}).get("reason", "signal")
                    if hasattr(signal, "meta") and signal.meta
                    else "signal"
                )
                self.journal.log_trade(
                    TradeRecord(
                        symbol=symbol,
                        strategy=self.strategy.__class__.__name__,
                        side="long",
                        entry_price=pos["entry_price"],
                        exit_price=price,
                        size=pos["size"],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=trade_meta.get("exit_reason", "signal"),
                        reasoning=getattr(signal, "reason", "") or "",
                        stop_price=pos.get("stop"),
                        raw_metadata=json.dumps(trade_meta),
                    )
                )

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

                # Update wiki feedback outcome
                if "wiki_feedback_id" in pos:
                    try:
                        outcome = "win" if pnl > 0 else "loss"
                        updated = self.journal.update_wiki_feedback(
                            pos["wiki_feedback_id"], outcome, pnl, pnl_pct
                        )
                        if updated:
                            logger.debug(
                                f"Wiki feedback {pos['wiki_feedback_id']} updated: {outcome}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to update wiki feedback: {e}")

                # Periodically adjust wiki min_alignment based on feedback
                try:
                    stats = self.journal.get_wiki_feedback_stats(min_samples=10)
                    if stats["accuracy"] is not None and hasattr(
                        self.strategy, "wiki_validator"
                    ):
                        self.strategy.wiki_validator.update_min_alignment_from_feedback(
                            stats
                        )
                except Exception as e:
                    logger.debug(f"Wiki feedback stats check failed: {e}")

    def _execute_partial_exit(self, symbol: str, exit_info: dict, bar):
        """Execute a partial exit (scale-out) order."""
        price = bar["close"]
        size = exit_info["size"]
        pos = self.positions.get(symbol)
        if not pos or pos["side"] != "long" or size <= 0:
            return

        order = self.order_manager.create_order(
            symbol=symbol,
            side=OrderSide.SELL,
            amount=size,
            order_type=OrderType.MARKET,
            strategy_name=self.strategy.__class__.__name__,
            reason=f"partial_exit_{exit_info['label']}",
        )
        result = self.order_retry.execute(
            self.order_manager.submit, order, last_price=price
        )

        if result.success:
            pnl = (price - pos["entry_price"]) * size
            pos["size"] -= size
            self.capital += size * price * 0.999
            logger.info(
                f"📐 PARTIAL EXIT {symbol} | {exit_info['label']} | "
                f"Size: {size:.6f} | P&L: ${pnl:.2f} | Remaining: {pos['size']:.6f}"
            )
            self.alerter.send_trade_closed(
                symbol=symbol,
                side="long",
                entry=pos["entry_price"],
                exit_price=price,
                pnl=pnl,
                pnl_pct=(price - pos["entry_price"]) / pos["entry_price"],
                exit_reason=f"partial_{exit_info['label']}",
            )
            # Remove position if fully exited
            if pos["size"] <= 0:
                del self.positions[symbol]
                self.trailing_stop.remove_position(symbol)
                self.partial_exit.remove_position(symbol)

    def _update_equity(self, symbol: str, bar):
        """Recalculate total equity and update position unrealized P&L."""
        current_price = bar["close"]
        with self._lock:
            for p in self.positions.values():
                if p["symbol"] == symbol:
                    p["current_price"] = current_price
                    p["unrealized_pnl"] = (current_price - p["entry_price"]) * p["size"]
                    p["unrealized_pnl_pct"] = (current_price - p["entry_price"]) / p[
                        "entry_price"
                    ]
            position_value = sum(
                p["size"] * current_price for p in self.positions.values()
            )
            self.equity = self.capital + position_value

    def _snapshot(self):
        """Record equity snapshot to journal."""
        exposure = sum(
            p.get("size", 0) * p.get("entry_price", 0) for p in self.positions.values()
        )
        peak = self.risk.guard.peak or self.equity
        dd = (peak - self.equity) / peak if peak > 0 else 0

        self.journal.snapshot(
            EquitySnapshot(
                equity=self.equity,
                cash=self.capital,
                open_positions=len(self.positions),
                open_exposure=exposure,
                drawdown_pct=dd,
                daily_pnl=0,  # calculated separately
            )
        )

    def _send_daily_summary(self):
        """Send daily P&L summary via Telegram using DailyReportGenerator."""
        try:
            self.daily_report.generate_and_notify(alerter=self.alerter)
            logger.info("Daily report sent")
        except Exception:
            # Fallback to simple summary
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
        with self._lock:
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
        # ruff: noqa: E402
        with self._lock:
            positions_copy = [
                {
                    "symbol": p.get("symbol", ""),
                    "side": p.get("side", ""),
                    "entry_price": p.get("entry_price", 0.0),
                    "size": p.get("size", 0.0),
                    "current_price": p.get("current_price"),
                    "unrealized_pnl": p.get("unrealized_pnl"),
                    "stop_price": p.get("stop"),
                    "strategy": self.strategy.__class__.__name__,
                    "entry_time": (
                        p.get("entry_time", "").isoformat()
                        if p.get("entry_time")
                        else None
                    ),
                    "meta": p.get("meta", {}),
                }
                for p in self.positions.values()
            ]
            status = {
                "mode": self.mode,
                "running": self.is_running,
                "equity": self.equity,
                "capital": self.capital,
                "open_positions": len(self.positions),
                "positions": positions_copy,
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
        # Add trailing stops
        status["trailing_stops"] = self.trailing_stop.summary()
        # Add partial exits
        status["partial_exits"] = self.partial_exit.summary()
        # Add slippage summary
        status["slippage"] = self.slippage_tracker.summary()
        # Add order retry stats
        status["order_retry"] = self.order_retry.get_stats()
        # Add correlation guard
        status["correlation"] = self.correlation_guard.summary()
        # Add sub-strategy state (regime, sub-signals, wiki alignment)
        if hasattr(self.strategy, "last_status") and self.strategy.last_status:
            status["sub_strategy"] = self.strategy.last_status
        if hasattr(self.strategy, "current_regime"):
            status["current_regime"] = self.strategy.current_regime
        if hasattr(self.strategy, "current_directional_regime"):
            status["directional_regime"] = self.strategy.current_directional_regime
        if hasattr(self.strategy, "regime_distribution"):
            status["regime_distribution"] = self.strategy.regime_distribution
        return status


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Live Trading Engine")
    parser.add_argument("--config", default="config/system.yaml")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="List of trading pairs (overrides config)",
    )
    parser.add_argument(
        "--strategy",
        default="RegimeEnsemble",
        choices=["RegimeEnsemble", "EMA-Trend", "Monthly-Breakout"],
    )
    parser.add_argument(
        "--health-port", type=int, default=None, help="Override health server port"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Override mode from CLI
    config["system"]["mode"] = args.mode

    # Override symbols if provided via CLI
    symbols = args.symbols
    if symbols is not None:
        pass  # Use CLI --symbols
    elif "--symbol" in sys.argv:
        symbols = [args.symbol]  # Use CLI --symbol
    else:
        symbols = config.get("data", {}).get("symbols", ["BTC/USDT"])  # Use config

    # Override health port if provided
    if args.health_port is not None:
        config.setdefault("monitoring", {})
        config["monitoring"]["health_port"] = args.health_port

    # Import strategy dynamically from registry
    strategy = None
    if config.get("strategies") and config["strategies"].get("registry"):
        for entry in config["strategies"]["registry"]:
            if entry["name"] == args.strategy:
                module_path = entry["module"]
                class_name = entry["class"]
                params = entry.get("params", {})
                module = __import__(module_path, fromlist=[class_name])
                strategy_class = getattr(module, class_name)
                strategy = strategy_class(params=params) if params else strategy_class()
                break

    if strategy is None:
        # Fallback for backward compatibility
        if args.strategy == "RegimeEnsemble":
            from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy

            strategy = RegimeEnsembleStrategy(
                params=config["strategies"]["registry"][2]["params"]
            )
        else:
            from strategies.rule_based.ema_trend import EMATrendStrategy

            strategy = EMATrendStrategy()

    engine = LiveTradingEngine(
        config=config,
        strategy=strategy,
        mode=args.mode,
        symbols=symbols,
    )

    try:
        engine.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        engine.stop()


if __name__ == "__main__":
    main()
