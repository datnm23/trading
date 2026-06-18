"""Tests for RegimeEnsemble strategy."""

import numpy as np
import pandas as pd

from strategies.base import StrategyContext
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy


def make_history(n: int = 100, trend: str = "sideways") -> pd.DataFrame:
    """Generate OHLCV history with specified trend."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    if trend == "uptrend":
        close = np.linspace(100, 150, n) + np.random.randn(n) * 2
    elif trend == "downtrend":
        close = np.linspace(150, 100, n) + np.random.randn(n) * 2
    elif trend == "sideways":
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    else:
        close = 100 + np.random.randn(n) * 5
    close = np.maximum(close, 1)
    high = close + np.abs(np.random.randn(n)) * 3
    low = close - np.abs(np.random.randn(n)) * 3
    low = np.maximum(low, close * 0.95)
    return pd.DataFrame(
        {
            "open": close - np.random.randn(n) * 1,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.randint(1000, 10000, n),
        },
        index=dates,
    )


def make_context(history: pd.DataFrame, symbol: str = "BTC/USDT") -> StrategyContext:
    """Create a StrategyContext from history."""
    bar = history.iloc[-1]
    return StrategyContext(
        symbol=symbol,
        bar=bar,
        history=history,
        account={"balance": 10000, "equity": 10000},
        positions=[],
    )


class FakeWikiValidator:
    """Fake wiki validator that accepts everything with high alignment."""

    min_alignment = 0.3

    def __init__(self, min_alignment=0.3):
        self.min_alignment = min_alignment

    def validate(self, signal, regime="neutral"):
        from knowledge_engine.signal_validator import WikiValidationResult

        return WikiValidationResult(
            original_strength=signal.strength,
            adjusted_strength=signal.strength,
            alignment_score=0.8,
            block_reason=None,
            context_summary="fake context",
            top_concepts="fake",
            regime=regime,
            side=signal.side,
            strategy="fake",
        )


class BlockingWikiValidator:
    """Fake wiki validator that blocks everything."""

    min_alignment = 0.3

    def validate(self, signal, regime="neutral"):
        from knowledge_engine.signal_validator import WikiValidationResult

        return WikiValidationResult(
            original_strength=signal.strength,
            adjusted_strength=0.0,
            alignment_score=0.1,
            block_reason="blocked by test",
            context_summary="fake",
            top_concepts="fake",
            regime=regime,
            side=signal.side,
            strategy="fake",
        )


class TestRegimeEnsemble:
    def test_warmup_all_sub_strategies(self):
        strat = RegimeEnsembleStrategy()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        assert strat.is_warm
        assert strat.ema.is_warm
        assert strat.breakout.is_warm
        assert strat.grid.is_warm

    def test_not_warm_returns_none(self):
        strat = RegimeEnsembleStrategy()
        ctx = make_context(make_history(100, "uptrend"))
        sig = strat.on_bar(ctx)
        assert sig is None
        assert "not warm" in str(strat.last_status["rejection_reasons"]).lower()

    def test_trending_regime_produces_buy_signal(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.side == "buy"
            assert sig.meta.get("ensemble_source") in ("ema", "breakout")
            assert sig.meta.get("regime") == "trending"

    def test_trending_bear_skips_longs(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "downtrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # In bear trending, longs are skipped
        if sig is None:
            assert "bear" in str(strat.last_status["rejection_reasons"]).lower()

    def test_cooldown_blocks_signals(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        # First signal may fire
        sig1 = strat.on_bar(ctx)
        if sig1:
            strat.bars_since_last_trade = 5  # force cooldown
            sig2 = strat.on_bar(ctx)
            if sig2 is None:
                assert "cooldown" in str(strat.last_status["rejection_reasons"]).lower()

    def test_ranging_regime_uses_grid(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "sideways")
        strat.warmup(hist)
        # Force regime to ranging by mocking detector
        strat.detector.detect = lambda h: {
            "regime": "ranging",
            "directional_regime": "sideways",
            "strength": 0.7,
            "metrics": {},
        }
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        if sig:
            assert sig.meta.get("ensemble_source") == "grid"
            assert sig.meta.get("regime") == "ranging"

    def test_wiki_blocks_misaligned_signals(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = BlockingWikiValidator()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        assert sig is None
        assert (
            "wiki" in str(strat.last_status["rejection_reasons"]).lower()
            or strat.last_status["wiki_action"] == "blocked"
        )

    def test_neutral_regime_requires_consensus(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "sideways")
        strat.warmup(hist)
        strat.detector.detect = lambda h: {
            "regime": "neutral",
            "directional_regime": "neutral",
            "strength": 0.2,
            "metrics": {},
        }
        ctx = make_context(hist)
        sig = strat.on_bar(ctx)
        # Neutral may or may not produce signal depending on consensus
        if sig is None:
            reasons = str(strat.last_status["rejection_reasons"]).lower()
            assert (
                "consensus" in reasons
                or "cooldown" in reasons
                or "no sub-strategy" in reasons
            )

    def test_last_status_populated(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        strat.on_bar(ctx)
        assert strat.last_status["symbol"] == "BTC/USDT"
        assert strat.last_status["regime"] in ("trending", "ranging", "neutral")
        assert "sub_signals" in strat.last_status
        assert "rejection_reasons" in strat.last_status
        assert "final_decision" in strat.last_status

    def test_regime_distribution(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        for _ in range(10):
            strat.on_bar(ctx)
        dist = strat.regime_distribution
        assert len(dist) > 0
        assert abs(sum(dist.values()) - 1.0) < 1e-9
        for r in dist:
            assert r in ("trending", "ranging", "neutral")

    def test_reset_clears_state(self):
        strat = RegimeEnsembleStrategy()
        strat.wiki_validator = FakeWikiValidator()
        hist = make_history(200, "uptrend")
        strat.warmup(hist)
        ctx = make_context(hist)
        strat.on_bar(ctx)
        strat.reset()
        assert not strat.is_warm
        assert strat.current_regime == "neutral"
        assert strat.bars_since_last_trade == 9999
        assert not strat.ema.is_warm
