"""Integrate Turtle Trading Wiki knowledge into signal validation.

Uses RAG to query wiki concepts for each trading signal and computes
an alignment score. Signals that contradict wiki principles are
downgraded or blocked.

Concepts applied:
    - vao_khi_co_loi_the (only trade when you have edge)
    - trend_following vs mean_reversion regime matching
    - cat_lo_nghiem_ngat (strict stop loss)
    - tam_ly_bam_viu_hy_vong (don't hope, follow rules)
"""

from typing import Optional
from dataclasses import dataclass

from loguru import logger

from strategies.base import Signal
from knowledge_engine.rag import WikiRAG


@dataclass
class WikiValidationResult:
    """Result of validating a signal against wiki knowledge."""
    original_strength: float
    adjusted_strength: float
    alignment_score: float   # 0.0 - 1.0
    block_reason: Optional[str] = None
    context_summary: str = ""
    top_concepts: str = ""   # Comma-separated concept titles
    regime: str = "neutral"
    side: str = ""
    strategy: str = ""


class WikiSignalValidator:
    """Validate trading signals against Turtle Trading Wiki knowledge.

    Usage:
        validator = WikiSignalValidator()
        result = validator.validate(signal, regime="trending")
        if result.block_reason:
            # Skip this signal
        else:
            signal.strength = result.adjusted_strength
    """

    def __init__(self, rag: Optional[WikiRAG] = None, min_alignment: float = 0.3):
        self.rag = rag or WikiRAG()
        self.base_min_alignment = min_alignment
        self.min_alignment = min_alignment
        self._build_index_if_needed()
        self._recent_feedback: List[dict] = []
        self._feedback_window = 50

    def update_min_alignment_from_feedback(self, stats: dict):
        """Dynamically adjust min_alignment based on feedback accuracy.
        
        If accuracy is low (< 0.55), lower threshold to allow more signals.
        If accuracy is high (> 0.75), raise threshold to be more selective.
        """
        acc = stats.get("accuracy")
        if acc is None:
            return
        old = self.min_alignment
        if acc < 0.55:
            self.min_alignment = max(0.15, self.min_alignment - 0.05)
        elif acc > 0.75:
            self.min_alignment = min(0.50, self.min_alignment + 0.02)
        if old != self.min_alignment:
            logger.info(f"Wiki min_alignment adjusted: {old:.2f} → {self.min_alignment:.2f} (accuracy={acc:.2%})")

    def _build_index_if_needed(self):
        if not self.rag._is_built:
            self.rag.build_index()

    def validate(self, signal: Signal, regime: str = "neutral") -> WikiValidationResult:
        """Validate a signal against wiki knowledge.

        Steps:
            1. Query wiki for context about the signal + regime
            2. Compute alignment score based on concept relevance
            3. Adjust signal strength or block if misaligned
        """
        query = self._build_query(signal, regime)
        
        # Get both context string and raw search results for concept tracking
        search_results = self.rag.search(query)
        context = self.rag.get_context(query, max_chars=2000)
        
        # Extract top concept titles
        top_concepts = ", ".join([r["document"]["title"] for r in search_results[:3]]) if search_results else ""
        
        meta = signal.meta or {}
        strategy = meta.get("ensemble_source", meta.get("strategy", "unknown"))

        if not context:
            logger.warning("Wiki context empty, allowing signal with no adjustment")
            return WikiValidationResult(
                original_strength=signal.strength,
                adjusted_strength=signal.strength,
                alignment_score=0.5,
                context_summary="",
                top_concepts=top_concepts,
                regime=regime,
                side=signal.side,
                strategy=strategy,
            )

        alignment = self._compute_alignment(signal, regime, context)
        block_reason = None
        adjusted = signal.strength * alignment
        wiki_action = "accepted"

        # Hard blocks
        if alignment < self.min_alignment:
            block_reason = (
                f"Signal misaligned with wiki knowledge (score={alignment:.2f}). "
                f"Regime={regime}, side={signal.side}. Context suggests caution."
            )
            adjusted = 0.0
            wiki_action = "blocked"
            logger.warning(f"BLOCKED by wiki: {block_reason}")

        # Downgrade weak alignments
        elif alignment < 0.5:
            wiki_action = "downgraded"
            logger.info(
                f"Signal downgraded: strength {signal.strength:.2f} → {adjusted:.2f} "
                f"(alignment={alignment:.2f})"
            )

        return WikiValidationResult(
            original_strength=signal.strength,
            adjusted_strength=adjusted,
            alignment_score=alignment,
            block_reason=block_reason,
            context_summary=context[:300],
            top_concepts=top_concepts,
            regime=regime,
            side=signal.side,
            strategy=strategy,
        )

    def _build_query(self, signal: Signal, regime: str) -> str:
        """Build a RAG query from signal context."""
        side = signal.side
        meta = signal.meta or {}
        strategy = meta.get("ensemble_source", meta.get("strategy", "unknown"))

        # Core query: what does wiki say about this strategy in this regime?
        queries = [
            f"{strategy} strategy in {regime} market",
            f"when to {side} in {regime} regime",
        ]

        # Add specific concept queries based on signal metadata
        if "stop" in meta:
            queries.append("strict stop loss importance")
        if regime == "ranging" and side == "buy":
            queries.append("mean reversion strategy rules")
        if regime == "trending" and side == "buy":
            queries.append("trend following entry rules")

        return " ".join(queries)

    def _compute_alignment(self, signal: Signal, regime: str, context: str) -> float:
        """Compute alignment score between signal and wiki context.

        Uses keyword-based heuristic scoring (fast, no LLM needed).
        More aggressive penalties to actually block misaligned signals.
        """
        context_lower = context.lower()
        score = 0.35  # lower baseline — signals must prove alignment

        side = signal.side
        meta = signal.meta or {}
        strategy = meta.get("ensemble_source", meta.get("strategy", ""))

        # --- Regime-strategy alignment (MAJOR factor) ---
        if regime == "trending":
            if "trend" in context_lower or "breakout" in context_lower:
                score += 0.20
            if strategy in ("ema", "breakout"):
                score += 0.15
            if "mean reversion" in context_lower and strategy not in ("grid",):
                score -= 0.30  # STRONG penalty: using MR in trending regime
            if "sideway" in context_lower and strategy in ("ema", "breakout"):
                score -= 0.25  # penalty: TF strategy in sideway market

        elif regime == "ranging":
            if "mean reversion" in context_lower or "grid" in context_lower or "sideway" in context_lower:
                score += 0.20
            if strategy == "grid":
                score += 0.15
            if "trend following" in context_lower and strategy in ("ema", "breakout"):
                score -= 0.30  # STRONG penalty: TF in ranging regime
            if "breakout" in context_lower and strategy == "ema":
                score -= 0.10  # minor penalty

        elif regime == "neutral":
            if "neutral" in context_lower or "uncertain" in context_lower:
                score += 0.10
            if "strong trend" in context_lower or "clear direction" in context_lower:
                score -= 0.20  # penalty: trading in uncertain regime when wiki says clear

        # --- Stop-loss alignment (critical) ---
        if "stop loss" in context_lower or "cat lo" in context_lower or "cut loss" in context_lower:
            if meta.get("stop") or meta.get("stop_price"):
                score += 0.15  # has stop loss → good
            else:
                score -= 0.25  # STRONG penalty: no stop loss when wiki emphasizes it

        # --- Signal strength / conviction ---
        if signal.strength >= 0.8:
            score += 0.10
        elif signal.strength < 0.5:
            score -= 0.15  # weak signal without strong conviction

        # --- Context contains explicit warnings ---
        warning_phrases = [
            "avoid", "don't trade", "not recommended", "khong nen", "tran", "risky",
            "dangerous", "high risk", "overbought", "oversold", "bubbl", "crash",
        ]
        for phrase in warning_phrases:
            if phrase in context_lower:
                score -= 0.20
                break  # only apply once

        # --- Emotional / discipline keywords ---
        if "discipline" in context_lower or "ky luat" in context_lower or "patience" in context_lower:
            score += 0.05
        if "hope" in context_lower or "hy vong" in context_lower or "bam viu" in context_lower:
            score -= 0.10
        if "fomo" in context_lower or "greed" in context_lower or "fear" in context_lower:
            score -= 0.10

        # --- Risk management ---
        if "risk" in context_lower or "rui ro" in context_lower:
            if meta.get("atr") or meta.get("stop"):
                score += 0.05
            else:
                score -= 0.10

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))


class WikiAwareEnsembleMixin:
    """Mixin to add wiki validation to any strategy.

    Usage:
        class MyStrategy(WikiAwareEnsembleMixin, BaseStrategy):
            def on_bar(self, context):
                signal = self._generate_signal(context)
                if signal:
                    return self.validate_with_wiki(signal, regime="trending")
                return None
    """

    def __init__(self, *args, wiki_min_alignment: float = 0.3, **kwargs):
        super().__init__(*args, **kwargs)
        self.wiki_validator = WikiSignalValidator(min_alignment=wiki_min_alignment)

    def validate_with_wiki(self, signal: Signal, regime: str = "neutral") -> Optional[Signal]:
        """Validate signal and return adjusted signal or None if blocked."""
        result = self.wiki_validator.validate(signal, regime=regime)
        if result.block_reason:
            return None
        signal.strength = result.adjusted_strength
        if signal.meta is None:
            signal.meta = {}
        signal.meta["wiki_alignment"] = result.alignment_score
        signal.meta["wiki_context"] = result.context_summary
        return signal
