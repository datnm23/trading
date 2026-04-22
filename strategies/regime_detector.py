"""Market regime detector: trending vs ranging."""

import pandas as pd
import numpy as np


class RegimeDetector:
    """Detect whether market is trending or ranging."""

    def __init__(self, lookback: int = 30, atr_period: int = 14):
        self.lookback = lookback
        self.atr_period = atr_period

    def detect(self, history: pd.DataFrame) -> dict:
        """Return regime info for current bar.
        
        Returns dict with:
            - regime: 'trending' | 'ranging' | 'neutral'
            - strength: 0.0 to 1.0 (confidence)
            - metrics: dict of raw metrics
        """
        if len(history) < self.lookback + self.atr_period:
            return {"regime": "neutral", "strength": 0.0, "metrics": {}}

        window = history.iloc[-self.lookback:]

        # Price range vs ATR ratio (proxy for trendiness)
        price_range = window["high"].max() - window["low"].min()

        # ATR calculation
        h = history["high"].iloc[-self.atr_period:]
        l = history["low"].iloc[-self.atr_period:]
        c = history["close"].iloc[-self.atr_period:]
        prev_c = c.shift(1)
        tr1 = h - l
        tr2 = (h - prev_c).abs()
        tr3 = (l - prev_c).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=self.atr_period, adjust=False).mean().iloc[-1]

        # ADX-like: directional movement
        up_move = window["high"].diff().iloc[1:]
        down_move = -window["low"].diff().iloc[1:]
        plus_dm = ((up_move > down_move) & (up_move > 0)) * up_move
        minus_dm = ((down_move > up_move) & (down_move > 0)) * down_move

        atr_series = tr.ewm(span=self.atr_period, adjust=False).mean()
        plus_di = 100 * plus_dm.ewm(span=self.atr_period, adjust=False).mean() / atr_series
        minus_di = 100 * minus_dm.ewm(span=self.atr_period, adjust=False).mean() / atr_series
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)) * 100
        adx = dx.ewm(span=self.atr_period, adjust=False).mean().iloc[-1]

        # Metrics
        range_atr_ratio = price_range / (atr + 1e-10)
        ema20 = history["close"].ewm(span=20).mean().iloc[-1]
        ema50 = history["close"].ewm(span=50).mean().iloc[-1]
        ema_slope = abs(ema20 - ema50) / (history["close"].iloc[-1] + 1e-10)

        # Composite trending score
        trend_score = (
            0.4 * min(adx / 50.0, 1.0) +
            0.3 * min(range_atr_ratio / 5.0, 1.0) +
            0.3 * min(ema_slope * 50.0, 1.0)
        )

        if trend_score > 0.6:
            regime = "trending"
        elif trend_score < 0.3:
            regime = "ranging"
        else:
            regime = "neutral"

        return {
            "regime": regime,
            "strength": abs(trend_score - 0.45) * 2.2,  # distance from neutral
            "metrics": {
                "adx": float(adx),
                "range_atr_ratio": float(range_atr_ratio),
                "ema_slope": float(ema_slope),
                "trend_score": float(trend_score),
            }
        }
