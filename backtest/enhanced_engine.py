"""Enhanced backtest engine with Wiki validation + Psychological enforcement.

This extends the base BacktestEngine to include:
    - WikiSignalValidator: blocks/downgrades signals contradicting wiki knowledge
    - PsychologicalEnforcer: auto-pause, size reduction, daily limits

Usage:
    from backtest.enhanced_engine import EnhancedBacktestEngine
    engine = EnhancedBacktestEngine(
        use_wiki=True,       # Enable wiki validation
        use_psych=True,      # Enable psychological enforcement
        wiki_min_align=0.3,
        psych_config={...},
    )
    result = engine.run(data, strategy, risk)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger

from backtest.engine import BacktestEngine, BacktestResult, Trade
from strategies.base import BaseStrategy, Signal, StrategyContext
from risk.manager import RiskManager
from knowledge_engine.signal_validator import WikiSignalValidator, WikiValidationResult
from risk.psychology import PsychologicalEnforcer, PsychologicalState


@dataclass
class EnhancedBacktestResult(BacktestResult):
    """Extended result with wiki and psych stats."""
    wiki_blocked: int = 0
    wiki_downgraded: int = 0
    wiki_avg_alignment: float = 0.0
    psych_paused_bars: int = 0
    psych_size_reductions: int = 0
    psych_total_pnl: float = 0.0


class EnhancedBacktestEngine(BacktestEngine):
    """Backtest engine with Wiki + Psychology layers.

    Args:
        use_wiki: Enable wiki signal validation
        use_psych: Enable psychological enforcement
        wiki_min_align: Minimum alignment score to pass wiki check
        psych_config: Config dict for PsychologicalEnforcer
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        use_wiki: bool = True,
        use_psych: bool = True,
        wiki_min_align: float = 0.3,
        psych_config: Optional[dict] = None,
    ):
        super().__init__(initial_capital, commission, slippage)
        self.use_wiki = use_wiki
        self.use_psych = use_psych

        self.wiki_validator = WikiSignalValidator(min_alignment=wiki_min_align) if use_wiki else None
        self.psych_enforcer = PsychologicalEnforcer(psych_config or {}) if use_psych else None

        # Stats tracking
        self.wiki_blocked = 0
        self.wiki_downgraded = 0
        self.wiki_alignments = []
        self.psych_paused_bars = 0
        self.psych_size_reductions = 0

    def run(self, data: pd.DataFrame, strategy: BaseStrategy, risk_manager: RiskManager) -> EnhancedBacktestResult:
        """Run enhanced backtest."""
        strategy.reset()
        strategy.warmup(data.iloc[:100])

        for i in range(100, len(data)):
            bar = data.iloc[i]
            history = data.iloc[:i+1]

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

            # Psychological check
            if self.use_psych and self.psych_enforcer:
                psych_state = self.psych_enforcer.check_state()
                if psych_state.is_paused:
                    self.psych_paused_bars += 1
                    # Still update equity but skip signals
                    self._update_equity(bar)
                    self.equity_history.append({"timestamp": bar.name, "equity": self.equity})
                    continue

            # Get signal from strategy
            signal = strategy.on_bar(context)

            # Wiki validation
            if signal and self.use_wiki and self.wiki_validator:
                regime = getattr(strategy, "current_regime", "neutral")
                signal = self._apply_wiki_validation(signal, regime)

            # Execute signal
            if signal:
                psych_state = self.psych_enforcer.state if self.use_psych else None
                self._process_signal(signal, bar, risk_manager, status, psych_state)

            # Update equity
            self._update_equity(bar)
            self.equity_history.append({"timestamp": bar.name, "equity": self.equity})

        return self._build_enhanced_result()

    def _apply_wiki_validation(self, signal: Signal, regime: str) -> Optional[Signal]:
        """Validate signal against wiki and return adjusted signal or None."""
        result = self.wiki_validator.validate(signal, regime=regime)
        self.wiki_alignments.append(result.alignment_score)

        if result.block_reason:
            self.wiki_blocked += 1
            logger.debug(f"Wiki BLOCKED: {result.block_reason[:80]}")
            return None

        if result.adjusted_strength < signal.strength:
            self.wiki_downgraded += 1
            logger.debug(
                f"Wiki DOWNGRADED: {signal.side} {signal.symbol} "
                f"{signal.strength:.2f} → {result.adjusted_strength:.2f}"
            )

        signal.strength = result.adjusted_strength
        if signal.meta is None:
            signal.meta = {}
        signal.meta["wiki_alignment"] = result.alignment_score
        return signal

    def _process_signal(self, signal: Signal, bar: pd.Series, risk_manager: RiskManager, status: dict, psych_state: Optional[PsychologicalState]):
        """Process signal with optional psychological size multiplier."""
        # Apply psych size multiplier
        size_multiplier = psych_state.size_multiplier if psych_state else 1.0
        if size_multiplier < 1.0 and self.use_psych:
            self.psych_size_reductions += 1

        if signal.side == "buy":
            if not status["exposure_ok"]:
                return
            entry_price = bar["close"] * (1 + self.slippage)
            atr = signal.meta.get("atr") if signal.meta else None
            if atr and atr > 0:
                stop_price = risk_manager.stop.atr_based(entry_price, "buy", atr, multiplier=2.0)
            else:
                stop_price = entry_price * 0.95
            size = risk_manager.sizer.size(self.equity, entry_price, stop_price, atr=atr)
            if size <= 0:
                return

            # Apply psych multiplier
            if size_multiplier < 1.0:
                original = size
                size *= size_multiplier
                logger.debug(f"Psych reduced size: {original:.4f} → {size:.4f}")

            self.positions.append({
                "symbol": signal.symbol,
                "side": "long",
                "entry_price": entry_price,
                "size": size,
                "stop": stop_price,
                "entry_time": signal.timestamp,
            })
            self.capital -= size * entry_price * (1 + self.commission)

        elif signal.side == "sell":
            for pos in list(self.positions):
                if pos["symbol"] == signal.symbol and pos["side"] == "long":
                    exit_price = bar["close"] * (1 - self.slippage)
                    pnl = (exit_price - pos["entry_price"]) * pos["size"]
                    pnl -= pos["size"] * exit_price * self.commission
                    self.capital += pos["size"] * exit_price * (1 - self.commission)
                    self.trades.append(Trade(
                        entry_time=pos["entry_time"],
                        exit_time=signal.timestamp,
                        symbol=pos["symbol"],
                        side="long",
                        entry_price=pos["entry_price"],
                        exit_price=exit_price,
                        size=pos["size"],
                        pnl=pnl,
                        exit_reason="signal",
                    ))
                    self.positions.remove(pos)

                    # Update psychological state with P&L
                    if self.use_psych and self.psych_enforcer:
                        emotion = signal.meta.get("emotion") if signal.meta else None
                        self.psych_enforcer.check_state(pnl=pnl, emotion=emotion)

    def _build_enhanced_result(self) -> EnhancedBacktestResult:
        """Build result with wiki/psych stats."""
        base = self._build_result()

        wiki_avg = np.mean(self.wiki_alignments) if self.wiki_alignments else 0.0

        return EnhancedBacktestResult(
            equity_curve=base.equity_curve,
            trades=base.trades,
            total_return=base.total_return,
            sharpe=base.sharpe,
            max_drawdown=base.max_drawdown,
            winrate=base.winrate,
            profit_factor=base.profit_factor,
            wiki_blocked=self.wiki_blocked,
            wiki_downgraded=self.wiki_downgraded,
            wiki_avg_alignment=wiki_avg,
            psych_paused_bars=self.psych_paused_bars,
            psych_size_reductions=self.psych_size_reductions,
            psych_total_pnl=sum(t.pnl for t in self.trades),
        )
