#!/usr/bin/env python3
"""ML-based strategy adapter with Stop-Loss / Take-Profit management."""

from typing import Optional

import pandas as pd
import numpy as np
from loguru import logger

from strategies.base import BaseStrategy, Signal, StrategyContext
from ml.drift_detection import ModelDriftMonitor
from strategies.regime_detector import RegimeDetector


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


class MLStrategy(BaseStrategy):
    """Wrapper for any trained ML model to generate trading signals.

    Signals:
        - prediction_proba > threshold → buy
        - prediction_proba < (1 - threshold) → sell
        - neutral otherwise

    Stop-Loss / Take-Profit:
        - Configurable via params
        - Checked on every bar after entry
        - Exit reasons tracked in signal meta
    """

    def __init__(self, model_pipeline, name: str = "ML-Strategy", drift_monitor: Optional[ModelDriftMonitor] = None, use_trend_filter: bool = True):
        super().__init__(name=name, params={})
        self.pipeline = model_pipeline
        self.in_position = False
        self.warmup_bars = 60
        self.use_trend_filter = use_trend_filter
        self.detector = RegimeDetector(lookback=30, atr_period=14)

        # SL/TP state
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.take_price = 0.0
        self.position_size = 0.0

        # SL/TP config
        params = self.params or {}
        self.sl_method = params.get("sl_method", "atr")  # atr | fixed_pct | none
        self.sl_value = params.get("sl_value", 2.0)      # ATR multiplier or pct
        self.tp_method = params.get("tp_method", "atr")  # atr | fixed_pct | none
        self.tp_value = params.get("tp_value", 3.0)      # ATR multiplier or pct
        self.trailing_sl = params.get("trailing_sl", False)
        self.trailing_activation = params.get("trailing_activation", 0.02)

        # Drift monitoring
        self.drift_monitor = drift_monitor

    def warmup(self, history: pd.DataFrame) -> None:
        if len(history) < self.warmup_bars:
            logger.warning(f"ML strategy needs {self.warmup_bars} bars, got {len(history)}")
            return
        self.is_warm = True

    def reset(self) -> None:
        super().reset()
        self.in_position = False
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.take_price = 0.0
        self.position_size = 0.0

    def _compute_sl_tp(self, entry: float, bar: pd.Series, history: pd.DataFrame) -> tuple:
        """Compute stop-loss and take-profit prices."""
        stop = None
        take = None

        atr_val = None
        if "atr" in self.sl_method or "atr" in self.tp_method:
            if len(history) >= 15:
                atr_series = _atr(history["high"], history["low"], history["close"], 14)
                atr_val = atr_series.iloc[-1]

        if self.sl_method == "atr" and atr_val and atr_val > 0:
            stop = entry - atr_val * self.sl_value
        elif self.sl_method == "fixed_pct":
            stop = entry * (1 - self.sl_value)

        if self.tp_method == "atr" and atr_val and atr_val > 0:
            take = entry + atr_val * self.tp_value
        elif self.tp_method == "fixed_pct":
            take = entry * (1 + self.tp_value)

        return stop, take

    def _update_trailing_stop(self, bar: pd.Series) -> None:
        """Update trailing stop if activated."""
        if not self.trailing_sl or not self.in_position or self.stop_price <= 0:
            return
        current_high = bar["high"]
        profit_pct = (current_high - self.entry_price) / self.entry_price
        if profit_pct >= self.trailing_activation:
            new_stop = self.entry_price + (current_high - self.entry_price) * 0.5
            if new_stop > self.stop_price:
                self.stop_price = new_stop
                logger.debug(f"Trailing stop updated: {self.stop_price:.2f}")

    def on_bar(self, context: StrategyContext) -> Optional[Signal]:
        if not self.is_warm:
            return None
        if len(context.history) < self.warmup_bars:
            return None

        bar = context.bar
        high = bar["high"]
        low = bar["low"]
        close = bar["close"]

        # Check SL/TP for existing position FIRST
        if self.in_position:
            self._update_trailing_stop(bar)

            if self.stop_price and low <= self.stop_price:
                self.in_position = False
                return Signal(
                    timestamp=bar.name,
                    symbol=context.symbol,
                    side="sell",
                    strength=1.0,
                    price=self.stop_price,
                    meta={
                        "reason": "stop_loss",
                        "entry_price": self.entry_price,
                        "stop_price": self.stop_price,
                        "take_price": self.take_price,
                        "pnl_pct": (self.stop_price - self.entry_price) / self.entry_price,
                    },
                )

            if self.take_price and high >= self.take_price:
                self.in_position = False
                return Signal(
                    timestamp=bar.name,
                    symbol=context.symbol,
                    side="sell",
                    strength=1.0,
                    price=self.take_price,
                    meta={
                        "reason": "take_profit",
                        "entry_price": self.entry_price,
                        "stop_price": self.stop_price,
                        "take_price": self.take_price,
                        "pnl_pct": (self.take_price - self.entry_price) / self.entry_price,
                    },
                )

        # Get model prediction
        pred_df = self.pipeline.predict(context.history)
        latest = pred_df.iloc[-1]
        proba = latest["prediction_proba"]
        signal_val = latest["signal"]

        # Log to drift monitor
        if self.drift_monitor is not None:
            features = latest.drop(["prediction_proba", "signal"], errors="ignore")
            self.drift_monitor.log_prediction(
                features=features,
                confidence=float(proba),
                predicted=int(signal_val == 1),
                actual=None,  # Will be updated after bar closes
            )

        # Trend filter: only enter long when EMA20 >= EMA50 (bullish alignment)
        trend_ok = True
        if self.use_trend_filter and not self.in_position:
            hist = context.history
            if len(hist) >= 50:
                ema20 = hist["close"].ewm(span=20).mean().iloc[-1]
                ema50 = hist["close"].ewm(span=50).mean().iloc[-1]
                trend_ok = ema20 >= ema50
                if not trend_ok:
                    logger.debug(f"ML trend filter blocked BUY: ema20={ema20:.2f} < ema50={ema50:.2f}")

        # Entry
        if signal_val == 1 and not self.in_position and trend_ok:
            self.in_position = True
            self.entry_price = close
            stop, take = self._compute_sl_tp(close, bar, context.history)
            self.stop_price = stop if stop else 0.0
            self.take_price = take if take else 0.0
            return Signal(
                timestamp=bar.name,
                symbol=context.symbol,
                side="buy",
                strength=float(proba),
                price=close,
                meta={
                    "reason": "entry",
                    "proba": float(proba),
                    "threshold": self.pipeline.threshold,
                    "stop_price": self.stop_price,
                    "take_price": self.take_price,
                },
            )

        # Model-driven exit
        elif signal_val == -1 and self.in_position:
            self.in_position = False
            return Signal(
                timestamp=bar.name,
                symbol=context.symbol,
                side="sell",
                strength=float(1 - proba),
                price=close,
                meta={
                    "reason": "signal_exit",
                    "entry_price": self.entry_price,
                    "pnl_pct": (close - self.entry_price) / self.entry_price,
                },
            )

        return None
