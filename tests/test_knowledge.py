"""Tests for knowledge engine signal validator."""

import pytest
from strategies.base import Signal
from knowledge_engine.signal_validator import WikiSignalValidator, WikiValidationResult


class TestWikiSignalValidator:
    def test_alignment_computation_trending(self):
        """Test alignment score for trending regime."""
        validator = WikiSignalValidator()
        signal = Signal(
            timestamp=pytest.importorskip("pandas").Timestamp("2026-01-01"),
            symbol="BTC/USDT",
            side="buy",
            strength=0.8,
            meta={"ensemble_source": "ema", "stop": 60000, "atr": 1000},
        )
        score = validator._compute_alignment(signal, "trending", "trend following strategy entry rules")
        assert score > 0.5

    def test_alignment_computation_ranging_penalty(self):
        """Test penalty for trend-following in ranging regime."""
        validator = WikiSignalValidator()
        signal = Signal(
            timestamp=pytest.importorskip("pandas").Timestamp("2026-01-01"),
            symbol="BTC/USDT",
            side="buy",
            strength=0.8,
            meta={"ensemble_source": "ema"},
        )
        score = validator._compute_alignment(
            signal, "ranging", "mean reversion strategy for sideway market"
        )
        # EMA strategy in ranging should get penalty vs trending
        assert score < 0.7

    def test_block_misaligned_signal(self):
        """Test that very low alignment signals are blocked."""
        validator = WikiSignalValidator(min_alignment=0.9)  # very strict
        signal = Signal(
            timestamp=pytest.importorskip("pandas").Timestamp("2026-01-01"),
            symbol="BTC/USDT",
            side="buy",
            strength=0.5,
            meta={"ensemble_source": "unknown"},
        )
        result = validator.validate(signal, regime="neutral")
        assert result.block_reason is not None
        assert result.adjusted_strength == 0.0

    def test_allow_aligned_signal(self):
        """Test that aligned signals pass through."""
        validator = WikiSignalValidator(min_alignment=0.1)
        signal = Signal(
            timestamp=pytest.importorskip("pandas").Timestamp("2026-01-01"),
            symbol="BTC/USDT",
            side="buy",
            strength=0.8,
            meta={"ensemble_source": "ema", "stop": 60000, "atr": 1000},
        )
        # Mock context that supports trend
        import unittest.mock
        with unittest.mock.patch.object(
            validator.rag, "get_context", return_value="trend following strategy use EMA"
        ):
            result = validator.validate(signal, regime="trending")
            assert result.block_reason is None
            assert result.adjusted_strength > 0

    def test_downgrade_weak_alignment(self):
        """Test that weak alignment downgrades strength."""
        validator = WikiSignalValidator(min_alignment=0.1)
        signal = Signal(
            timestamp=pytest.importorskip("pandas").Timestamp("2026-01-01"),
            symbol="BTC/USDT",
            side="buy",
            strength=0.8,
            meta={"ensemble_source": "grid"},
        )
        import unittest.mock
        with unittest.mock.patch.object(
            validator.rag, "get_context", return_value="mean reversion grid strategy"
        ):
            result = validator.validate(signal, regime="trending")
            assert result.adjusted_strength < signal.strength
