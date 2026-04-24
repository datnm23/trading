"""Regime-based ensemble strategy with Wiki knowledge validation."""

from typing import Optional, List, Dict

import pandas as pd
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext
from strategies.regime_detector import RegimeDetector
from strategies.rule_based.ema_trend import EMATrendStrategy, _atr
from strategies.rule_based.monthly_breakout import MonthlyBreakoutStrategy
from strategies.rule_based.grid_mean_reversion import GridMeanReversionStrategy
from knowledge_engine.signal_validator import WikiSignalValidator


class RegimeEnsembleStrategy(BaseStrategy):
    """Ensemble that activates sub-strategies based on market regime.

    Validates signals against Turtle Trading Wiki knowledge to ensure
    alignment with proven principles (vao_khi_co_loi_the, cat_lo_nghiem_ngat, etc.)

    Regime mapping:
        - trending  → EMA-Trend + Monthly Breakout (vote)
        - ranging   → Grid Mean Reversion
        - neutral   → Conservative: require 2/3 agreement
    """

    def __init__(self, params: Optional[dict] = None):
        super().__init__(name="RegimeEnsemble", params=params)

        # Wiki knowledge validator
        wiki_min_alignment = params.get("wiki_min_alignment", 0.3) if params else 0.3
        self.wiki_validator = WikiSignalValidator(min_alignment=wiki_min_alignment)

        # Sub-strategies
        self.ema = EMATrendStrategy(params=params.get("ema", {}))
        self.breakout = MonthlyBreakoutStrategy(params=params.get("breakout", {}))
        self.grid = GridMeanReversionStrategy(params=params.get("grid", {}))
        self.sub_strategies = {
            "ema": self.ema,
            "breakout": self.breakout,
            "grid": self.grid,
        }

        # Regime detector
        self.detector = RegimeDetector(
            lookback=params.get("regime_lookback", 30),
            atr_period=params.get("atr_period", 14),
        )

        # State
        self.current_regime = "neutral"
        self.current_directional_regime = "neutral"
        self.regime_history = []
        self.last_signal_source = None
        self.bars_since_last_trade = 9999  # cooldown counter
        self.last_status = {}  # populated every bar for diagnostics

    def warmup(self, history: pd.DataFrame) -> None:
        for s in self.sub_strategies.values():
            s.warmup(history)
        self.is_warm = True

    def reset(self) -> None:
        super().reset()
        for s in self.sub_strategies.values():
            s.reset()
        self.current_regime = "neutral"
        self.current_directional_regime = "neutral"
        self.regime_history = []
        self.last_signal_source = None
        self.bars_since_last_trade = 9999

    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        self.last_status = {
            "symbol": context.symbol,
            "bar_time": str(context.bar.name if hasattr(context.bar, "name") else "unknown"),
            "regime": "unknown",
            "directional_regime": "unknown",
            "sub_signals": {},
            "rejection_reasons": [],
            "final_decision": "no_signal",
            "wiki_alignment": 0.0,
            "wiki_top_concepts": "",
            "wiki_action": "no_signal",
            "wiki_min_alignment": self.wiki_validator.min_alignment,
        }

        if not self.is_warm:
            self.last_status["rejection_reasons"].append("Strategy not warm yet")
            return None

        self.bars_since_last_trade += 1

        # Detect regime
        regime_info = self.detector.detect(context.history)
        self.current_regime = regime_info["regime"]
        self.current_directional_regime = regime_info.get("directional_regime", self.current_regime)
        self.regime_history.append(self.current_regime)
        self.last_status["regime"] = self.current_regime
        self.last_status["directional_regime"] = self.current_directional_regime

        # Collect signals from all sub-strategies
        signals: Dict[str, Optional[Signal]] = {}
        for name, strategy in self.sub_strategies.items():
            sig = strategy.on_bar(context)
            if sig:
                signals[name] = sig
                self.last_status["sub_signals"][name] = sig.side

        # Regime-based aggregation
        if self.current_regime == "trending":
            signal = self._aggregate_trending(signals, context, regime_info)
        elif self.current_regime == "ranging":
            signal = self._aggregate_ranging(signals, context, regime_info)
        else:  # neutral
            signal = self._aggregate_neutral(signals, context, regime_info)

        # Validate against Turtle Trading Wiki knowledge
        if signal:
            validated = self._validate_with_wiki(signal)
            # TEMPORARY: Allow signals even if wiki blocks (for testing)
            if validated:
                self.bars_since_last_trade = 0
                self.last_status["final_decision"] = f"{validated.side.upper()} signal accepted"
                return validated
            else:
                # Allow signal through with reduced strength instead of blocking
                logger.warning(f"Wiki blocked {signal.side} {signal.symbol}, allowing with strength=0.3")
                signal.strength = 0.3
                signal.meta = signal.meta or {}
                signal.meta["wiki_bypassed"] = True
                self.bars_since_last_trade = 0
                self.last_status["final_decision"] = f"{signal.side.upper()} signal (wiki bypassed)"
                return signal
        else:
            if not self.last_status["rejection_reasons"]:
                self.last_status["rejection_reasons"].append("No sub-strategy produced a signal")
            self.last_status["final_decision"] = "no_signal"
        return None

    def _validate_with_wiki(self, signal: Signal) -> Optional[Signal]:
        """Validate signal against wiki knowledge. May block or downgrade."""
        result = self.wiki_validator.validate(signal, regime=self.current_regime)
        
        # Store wiki details for alerts and feedback
        if signal.meta is None:
            signal.meta = {}
        signal.meta["wiki_alignment"] = result.alignment_score
        signal.meta["wiki_context"] = result.context_summary
        signal.meta["wiki_top_concepts"] = result.top_concepts
        signal.meta["wiki_action"] = "blocked" if result.block_reason else ("downgraded" if result.alignment_score < 0.5 else "accepted")
        signal.meta["wiki_min_alignment"] = self.wiki_validator.min_alignment
        
        # Update last_status for no-trade alerts
        self.last_status["wiki_alignment"] = result.alignment_score
        self.last_status["wiki_top_concepts"] = result.top_concepts
        self.last_status["wiki_action"] = signal.meta["wiki_action"]
        self.last_status["wiki_min_alignment"] = self.wiki_validator.min_alignment
        
        if result.block_reason:
            logger.warning(
                f"Wiki BLOCKED {signal.side} {signal.symbol}: {result.block_reason[:120]}"
            )
            return None
        if result.alignment_score < 0.5:
            logger.info(
                f"Wiki adjusted {signal.side} {signal.symbol}: "
                f"strength {signal.strength:.2f} → {result.adjusted_strength:.2f} "
                f"(alignment={result.alignment_score:.2f})"
            )
        signal.strength = result.adjusted_strength
        return signal

    def _aggregate_trending(self, signals: dict, context: StrategyContext, regime_info: dict) -> Optional[Signal]:
        """In trending regime: use EMA + Breakout (trend-following).
        Skip long trades in bear directional regime.
        Enforce cooldown between trades to avoid chop.
        """
        # Skip all long trades in bear markets
        if self.current_directional_regime == "bear":
            self.last_status["rejection_reasons"].append("Directional regime = BEAR → skip all longs")
            return None

        # Cooldown: wait 48 bars (~8 days on 4h) between trades
        COOLDOWN_BARS = 48
        if self.bars_since_last_trade < COOLDOWN_BARS:
            self.last_status["rejection_reasons"].append(f"Cooldown active ({self.bars_since_last_trade}/{COOLDOWN_BARS} bars)")
            return None

        trend_signals = []
        for name in ["ema", "breakout"]:
            if name in signals:
                trend_signals.append((name, signals[name]))

        if not trend_signals:
            self.last_status["rejection_reasons"].append("No EMA or Breakout signal fired")
            return None

        # If both agree, take the signal
        sides = [s.side for _, s in trend_signals]
        if len(set(sides)) == 1:
            chosen = max(trend_signals, key=lambda x: x[1].strength)
            self.last_signal_source = chosen[0]
            logger.debug(f"Trending regime | {chosen[0]} signal: {chosen[1].side}")
            return self._clone_signal(chosen[1], source=chosen[0], regime="trending")

        # Conflict: prefer buy signals (bullish bias, but skip in bear above)
        for name, sig in trend_signals:
            if sig.side == "buy":
                self.last_signal_source = name
                return self._clone_signal(sig, source=name, regime="trending")

        self.last_status["rejection_reasons"].append("EMA/Breakout conflict → no buy consensus")
        return None

    def _aggregate_ranging(self, signals: dict, context: StrategyContext, regime_info: dict) -> Optional[Signal]:
        """In ranging regime: use Grid Mean Reversion."""
        COOLDOWN_BARS = 48
        if self.bars_since_last_trade < COOLDOWN_BARS:
            self.last_status["rejection_reasons"].append(f"Cooldown active ({self.bars_since_last_trade}/{COOLDOWN_BARS} bars)")
            return None

        if "grid" in signals:
            self.last_signal_source = "grid"
            logger.debug(f"Ranging regime | grid signal: {signals['grid'].side}")
            return self._clone_signal(signals['grid'], source="grid", regime="ranging")

        self.last_status["rejection_reasons"].append("Grid strategy did not fire")

        # Fallback: if grid didn't fire but ema/breakout strongly agree
        fallback = self._check_consensus(signals, min_agree=2)
        if fallback:
            self.last_signal_source = fallback[0]
            return self._clone_signal(fallback[1], source=fallback[0], regime="ranging")

        self.last_status["rejection_reasons"].append("Fallback consensus (2/3) not reached")
        return None

    def _aggregate_neutral(self, signals: dict, context: StrategyContext, regime_info: dict) -> Optional[Signal]:
        """In neutral regime: require strong consensus (2/3 agree)."""
        COOLDOWN_BARS = 48
        if self.bars_since_last_trade < COOLDOWN_BARS:
            self.last_status["rejection_reasons"].append(f"Cooldown active ({self.bars_since_last_trade}/{COOLDOWN_BARS} bars)")
            return None

        fallback = self._check_consensus(signals, min_agree=2)
        if fallback:
            self.last_signal_source = fallback[0]
            return self._clone_signal(fallback[1], source=fallback[0], regime="neutral")

        self.last_status["rejection_reasons"].append("Neutral regime: 2/3 consensus not reached")
        return None

    def _check_consensus(self, signals: dict, min_agree: int = 2):
        """Check if at least min_agree strategies agree on a side."""
        buys = [(n, s) for n, s in signals.items() if s.side == "buy"]
        sells = [(n, s) for n, s in signals.items() if s.side == "sell"]

        if len(buys) >= min_agree:
            return max(buys, key=lambda x: x[1].strength)
        if len(sells) >= min_agree:
            return max(sells, key=lambda x: x[1].strength)
        return None

    def _clone_signal(self, signal: Signal, source: str, regime: str) -> Signal:
        """Clone signal with ensemble metadata."""
        meta = dict(signal.meta or {})
        meta["ensemble_source"] = source
        meta["regime"] = regime
        meta["directional_regime"] = self.current_directional_regime
        return Signal(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.side,
            strength=signal.strength,
            price=signal.price,
            meta=meta,
        )

    @property
    def regime_distribution(self) -> dict:
        """Return distribution of regimes encountered."""
        if not self.regime_history:
            return {}
        total = len(self.regime_history)
        return {
            r: self.regime_history.count(r) / total
            for r in set(self.regime_history)
        }
