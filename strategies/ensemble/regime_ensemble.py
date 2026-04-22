"""Regime-based ensemble strategy with Wiki knowledge validation."""

from typing import Optional, List, Dict

import pandas as pd
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext
from strategies.regime_detector import RegimeDetector
from strategies.rule_based.ema_trend import EMATrendStrategy
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
        self.regime_history = []
        self.last_signal_source = None

    def warmup(self, history: pd.DataFrame) -> None:
        for s in self.sub_strategies.values():
            s.warmup(history)
        self.is_warm = True

    def reset(self) -> None:
        super().reset()
        for s in self.sub_strategies.values():
            s.reset()
        self.current_regime = "neutral"
        self.regime_history = []
        self.last_signal_source = None

    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        if not self.is_warm:
            return None

        # Detect regime
        regime_info = self.detector.detect(context.history)
        self.current_regime = regime_info["regime"]
        self.regime_history.append(self.current_regime)

        # Collect signals from all sub-strategies
        signals: Dict[str, Optional[Signal]] = {}
        for name, strategy in self.sub_strategies.items():
            sig = strategy.on_bar(context)
            if sig:
                signals[name] = sig

        # Regime-based aggregation
        if self.current_regime == "trending":
            signal = self._aggregate_trending(signals, context, regime_info)
        elif self.current_regime == "ranging":
            signal = self._aggregate_ranging(signals, context, regime_info)
        else:  # neutral
            signal = self._aggregate_neutral(signals, context, regime_info)

        # Validate against Turtle Trading Wiki knowledge
        if signal:
            return self._validate_with_wiki(signal)
        return None

    def _validate_with_wiki(self, signal: Signal) -> Optional[Signal]:
        """Validate signal against wiki knowledge. May block or downgrade."""
        result = self.wiki_validator.validate(signal, regime=self.current_regime)
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
        if signal.meta is None:
            signal.meta = {}
        signal.meta["wiki_alignment"] = result.alignment_score
        signal.meta["wiki_context"] = result.context_summary
        return signal

    def _aggregate_trending(self, signals: dict, context: StrategyContext, regime_info: dict) -> Optional[Signal]:
        """In trending regime: use EMA + Breakout (trend-following)."""
        trend_signals = []
        for name in ["ema", "breakout"]:
            if name in signals:
                trend_signals.append((name, signals[name]))

        if not trend_signals:
            return None

        # If both agree, take the signal
        sides = [s.side for _, s in trend_signals]
        if len(set(sides)) == 1:
            # All agree
            chosen = max(trend_signals, key=lambda x: x[1].strength)
            self.last_signal_source = chosen[0]
            logger.debug(f"Trending regime | {chosen[0]} signal: {chosen[1].side}")
            return self._clone_signal(chosen[1], source=chosen[0], regime="trending")

        # Conflict: prefer the one that doesn't fight the regime
        # If in strong uptrend, prefer buy signals
        if regime_info["metrics"]["ema_slope"] > 0:
            for name, sig in trend_signals:
                if sig.side == "buy":
                    self.last_signal_source = name
                    return self._clone_signal(sig, source=name, regime="trending")
        else:
            for name, sig in trend_signals:
                if sig.side == "sell":
                    self.last_signal_source = name
                    return self._clone_signal(sig, source=name, regime="trending")

        return None

    def _aggregate_ranging(self, signals: dict, context: StrategyContext, regime_info: dict) -> Optional[Signal]:
        """In ranging regime: use Grid Mean Reversion."""
        if "grid" in signals:
            self.last_signal_source = "grid"
            logger.debug(f"Ranging regime | grid signal: {signals['grid'].side}")
            return self._clone_signal(signals["grid"], source="grid", regime="ranging")

        # Fallback: if grid didn't fire but ema/breakout strongly agree
        fallback = self._check_consensus(signals, min_agree=2)
        if fallback:
            self.last_signal_source = fallback[0]
            return self._clone_signal(fallback[1], source=fallback[0], regime="ranging")
        return None

    def _aggregate_neutral(self, signals: dict, context: StrategyContext, regime_info: dict) -> Optional[Signal]:
        """In neutral regime: require strong consensus (2/3 agree)."""
        fallback = self._check_consensus(signals, min_agree=2)
        if fallback:
            self.last_signal_source = fallback[0]
            return self._clone_signal(fallback[1], source=fallback[0], regime="neutral")
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
