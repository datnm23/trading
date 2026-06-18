"""Tests for RegimeDetector."""

import numpy as np
import pandas as pd

from strategies.regime_detector import RegimeDetector


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


class TestRegimeDetector:
    def test_trending_uptrend(self):
        det = RegimeDetector(lookback=30, atr_period=14)
        hist = make_history(100, "uptrend")
        result = det.detect(hist)
        assert result["regime"] == "trending"
        assert result["directional_regime"] == "bull"
        assert result["strength"] > 0
        assert "metrics" in result
        assert "adx" in result["metrics"]
        assert "trend_score" in result["metrics"]

    def test_trending_downtrend(self):
        det = RegimeDetector(lookback=30, atr_period=14)
        hist = make_history(100, "downtrend")
        result = det.detect(hist)
        assert result["regime"] == "trending"
        assert result["directional_regime"] == "bear"

    def test_ranging_sideways(self):
        det = RegimeDetector(lookback=30, atr_period=14)
        hist = make_history(100, "sideways")
        result = det.detect(hist)
        # Sideways may be detected as ranging or neutral
        assert result["regime"] in ("ranging", "neutral")
        assert result["directional_regime"] in ("sideways", "neutral")

    def test_insufficient_data(self):
        det = RegimeDetector(lookback=50, atr_period=20)
        hist = make_history(10, "uptrend")
        result = det.detect(hist)
        assert result["regime"] == "neutral"
        assert result["strength"] == 0.0

    def test_metrics_present(self):
        det = RegimeDetector(lookback=30, atr_period=14)
        hist = make_history(100, "uptrend")
        result = det.detect(hist)
        metrics = result["metrics"]
        assert "adx" in metrics
        assert "atr" in metrics
        assert "range_atr_ratio" in metrics
        assert "ema_slope" in metrics
        assert "trend_score" in metrics
        assert metrics["atr"] > 0
        assert metrics["trend_score"] > 0
