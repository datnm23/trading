"""TA filter functions for VN Stock screener.

Each filter returns (passed: bool, value: float | None, label: str).
value=None signals N/A — engine excludes from score normalization.
Prices in OHLCV are in THOUSANDS of VND (as per vnstock convention).
"""

from typing import Optional, Tuple
import pandas as pd
from loguru import logger

FilterResult = Tuple[bool, Optional[float], str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_ma(series: pd.Series, period: int) -> Optional[float]:
    """Return the most recent simple moving average, or None if insufficient data."""
    if len(series) < period:
        return None
    return float(series.tail(period).mean())


# ---------------------------------------------------------------------------
# TA Filters
# ---------------------------------------------------------------------------

def filter_price_above_ma(
    ohlcv: pd.DataFrame,
    ma50_period: int = 50,
    ma200_period: int = 200,
) -> FilterResult:
    """Price > MA50 AND > MA200.

    Returns the ratio price/MA200 as value (useful for scoring gradient).
    N/A when insufficient history for MA200.
    """
    label = f"Price > MA{ma50_period} & MA{ma200_period}"
    if ohlcv.empty or "close" not in ohlcv.columns:
        logger.debug("Price/MA: N/A (empty OHLCV)")
        return False, None, label

    close = ohlcv["close"].dropna()
    if len(close) < ma200_period:
        logger.debug(f"Price/MA: N/A (only {len(close)} bars, need {ma200_period})")
        return False, None, label

    current_price = float(close.iloc[-1])
    ma50 = _compute_ma(close, ma50_period)
    ma200 = _compute_ma(close, ma200_period)

    if ma50 is None or ma200 is None:
        return False, None, label

    passed = current_price > ma50 and current_price > ma200
    # Value: price / MA200 ratio (>1 means above)
    value = current_price / ma200 if ma200 > 0 else None
    logger.debug(
        f"Price={current_price:.2f} MA50={ma50:.2f} MA200={ma200:.2f} "
        f"ratio={value:.3f} passed={passed}"
    )
    return passed, value, label


def filter_relative_strength(
    ohlcv: pd.DataFrame,
    index_ohlcv: Optional[pd.DataFrame],
    lookback_days: int = 60,
) -> FilterResult:
    """Relative strength of ticker vs VN-Index over N days.

    RS = (ticker_return - index_return) over lookback_days.
    Positive RS → outperforming the index.
    Degrades gracefully when index data is unavailable (returns N/A).
    """
    label = f"RS vs VN-Index ({lookback_days}d)"
    if ohlcv.empty or "close" not in ohlcv.columns:
        logger.debug("RS: N/A (empty ticker OHLCV)")
        return False, None, label

    close = ohlcv["close"].dropna()
    if len(close) < lookback_days + 1:
        logger.debug(f"RS: N/A (only {len(close)} bars, need {lookback_days + 1})")
        return False, None, label

    ticker_return = float(close.iloc[-1] / close.iloc[-(lookback_days + 1)] - 1)

    if index_ohlcv is None or index_ohlcv.empty:
        # Degrade: no index data — mark N/A, log warning
        logger.warning("RS: VN-Index data unavailable; marking N/A")
        return False, None, label

    idx_close = index_ohlcv["close"].dropna()
    if len(idx_close) < lookback_days + 1:
        logger.warning(f"RS: VN-Index has only {len(idx_close)} bars; marking N/A")
        return False, None, label

    index_return = float(idx_close.iloc[-1] / idx_close.iloc[-(lookback_days + 1)] - 1)
    rs = ticker_return - index_return
    passed = rs > 0.0
    logger.debug(f"ticker_ret={ticker_return:.2%} idx_ret={index_return:.2%} RS={rs:.2%} passed={passed}")
    return passed, rs, label


def filter_liquidity(
    ohlcv: pd.DataFrame,
    threshold: float,
    lookback_days: int = 20,
) -> FilterResult:
    """Average daily trading value (GTGD) over N days > threshold (VND absolute).

    GTGD = close (thousands VND) * 1000 * volume (shares).
    threshold is in absolute VND (e.g. 10_000_000_000 = 10 tỷ).
    """
    label = f"Avg GTGD {lookback_days}d > {threshold / 1e9:.0f} tỷ"
    if ohlcv.empty or not {"close", "volume"}.issubset(ohlcv.columns):
        logger.debug("Liquidity: N/A (empty OHLCV)")
        return False, None, label

    df = ohlcv[["close", "volume"]].dropna()
    if len(df) < lookback_days:
        logger.debug(f"Liquidity: N/A (only {len(df)} bars)")
        return False, None, label

    recent = df.tail(lookback_days)
    # close is in thousands VND → multiply by 1000 for absolute VND
    avg_value = float((recent["close"] * 1000 * recent["volume"]).mean())
    passed = avg_value > threshold
    logger.debug(f"Avg GTGD={avg_value / 1e9:.2f} tỷ threshold={threshold / 1e9:.2f} tỷ passed={passed}")
    return passed, avg_value, label
