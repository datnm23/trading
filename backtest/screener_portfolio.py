"""Portfolio and data-source helpers for the screener backtest.

Provides:
- AsOfDataSource: wraps StockDataSource, clips OHLCV to as_of date (no look-ahead).
- EqualWeightPortfolio: long-only equal-weight portfolio with per-side VN fee model.
- Curve/price utility functions used by the rebalance loop.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from data.vn.base import StockDataSource


# ---------------------------------------------------------------------------
# Point-in-time OHLCV slicer
# ---------------------------------------------------------------------------

def clip_ohlcv(df: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """Return rows of OHLCV where time <= as_of. Core no-look-ahead guard."""
    if df.empty:
        return df
    as_of_ts = pd.Timestamp(as_of)
    time_col = df["time"] if "time" in df.columns else df.index
    mask = pd.to_datetime(time_col) <= as_of_ts
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Point-in-time data source wrapper
# ---------------------------------------------------------------------------

class AsOfDataSource(StockDataSource):
    """Wraps any StockDataSource and enforces point-in-time price data.

    OHLCV is clipped to rows with time <= as_of_date.
    Financial statements and ratios pass through unchanged: they store
    historical period-keyed dicts, and the screener reads the most-recent
    available period — which is acceptable given the BCTC publication lag
    configured in backtest.yaml (bctc_publication_lag_days).

    Limitation: true point-in-time financial snapshots would require vnstock
    to serve data as it existed on a specific date, which is not available
    offline. The lag approximation is the documented mitigation.
    """

    def __init__(self, source: StockDataSource, as_of: date, lookback_days: int = 500) -> None:
        self._source = source
        self._as_of = as_of
        self._lookback_days = lookback_days

    def get_ohlcv(self, ticker: str, start: str, end: str, interval: str = "1D") -> pd.DataFrame:
        # Point-in-time window: the screener config uses a FIXED live-oriented
        # start_date (e.g. 2023-01-01); at a historical as_of that start can be
        # AFTER as_of → empty slice (the rows=0 bug). Anchor the window to as_of:
        # fetch [as_of - lookback, as_of] so technical indicators always have
        # history regardless of the caller's start. Take the earlier start so an
        # explicitly-earlier caller window is still honoured.
        as_of_str = self._as_of.isoformat()
        lookback_start = (self._as_of - timedelta(days=self._lookback_days)).isoformat()
        effective_start = min(start, lookback_start)
        effective_end = min(end, as_of_str)
        df = self._source.get_ohlcv(ticker, effective_start, effective_end, interval)
        return clip_ohlcv(df, self._as_of)

    def get_financials(self, ticker: str, statement_type: str, period: str = "year"):
        return self._source.get_financials(ticker, statement_type, period)

    def get_ratios(self, ticker: str, period: str = "year"):
        return self._source.get_ratios(ticker, period)

    def get_company(self, ticker: str):
        return self._source.get_company(ticker)


# ---------------------------------------------------------------------------
# Equal-weight portfolio with VN transaction fee model
# ---------------------------------------------------------------------------

class EqualWeightPortfolio:
    """Long-only equal-weight portfolio with per-side VN transaction fees.

    Fee model (conservative, VN market):
    - Every rebalance liquidates ALL holdings (sell fee on gross proceeds).
    - Buys new equal-weight positions (buy fee per position on gross cost).
    - Rationale: simplicity; avoids complex partial-rebalance accounting.
    - VN typical range: 0.15–0.35% per side; default config uses 30 bps.
    """

    def __init__(self, initial_capital: float, fee_bps: float) -> None:
        self._capital: float = initial_capital   # undeployed cash
        self._fee_bps: float = fee_bps           # per side in basis points
        self._holdings: Dict[str, float] = {}    # ticker → shares held
        self._total_fees: float = 0.0

    def rebalance(self, picks: List[str], prices: Dict[str, float]) -> None:
        """Liquidate all holdings → buy picks equally. Apply fees both sides."""
        if not picks:
            return
        fee_rate = self._fee_bps / 10_000.0

        # Liquidate: gross proceeds from current holdings minus sell fee
        gross_proceeds = sum(
            self._holdings.get(t, 0.0) * prices.get(t, 0.0)
            for t in self._holdings
        )
        sell_fee = gross_proceeds * fee_rate
        self._total_fees += sell_fee
        total_cash = self._capital + gross_proceeds - sell_fee

        # Filter to picks with valid prices
        valid_picks = [t for t in picks if prices.get(t, 0.0) > 0]
        if not valid_picks:
            logger.warning("No valid prices for any pick; holding cash.")
            self._holdings = {}
            self._capital = total_cash
            return

        # Buy equal-weight: each position gets (total_cash / n) gross, minus buy fee
        per_pos_gross = total_cash / len(valid_picks)
        new_holdings: Dict[str, float] = {}
        for ticker in valid_picks:
            price = prices[ticker]
            buy_fee = per_pos_gross * fee_rate
            self._total_fees += buy_fee
            new_holdings[ticker] = (per_pos_gross - buy_fee) / price

        self._holdings = new_holdings
        self._capital = 0.0  # fully deployed

    def value(self, prices: Dict[str, float]) -> float:
        """Mark-to-market value: holdings at current prices + undeployed cash."""
        return (
            sum(self._holdings.get(t, 0.0) * prices.get(t, 0.0) for t in self._holdings)
            + self._capital
        )

    @property
    def total_fees(self) -> float:
        """Cumulative fees paid in absolute currency units."""
        return self._total_fees


# ---------------------------------------------------------------------------
# Price and curve utilities
# ---------------------------------------------------------------------------

def get_prices_on_date(
    all_ohlcv: Dict[str, pd.DataFrame],
    tickers: List[str],
    as_of: date,
) -> Dict[str, float]:
    """Return the last available close price for each ticker on or before as_of."""
    as_of_ts = pd.Timestamp(as_of)
    prices: Dict[str, float] = {}
    for ticker in tickers:
        df = all_ohlcv.get(ticker, pd.DataFrame())
        if df.empty:
            continue
        subset = df[df["time"] <= as_of_ts]
        if not subset.empty:
            prices[ticker] = float(subset["close"].iloc[-1])
    return prices


def build_benchmark_curve(
    source: StockDataSource,
    symbol: str,
    all_dates: pd.DatetimeIndex,
    start_str: str,
    end_str: str,
) -> pd.Series:
    """Fetch benchmark OHLCV and build a normalised (start=1.0) close series.

    Returns an empty Series on failure — caller should fall back to equal-weight.
    """
    try:
        df = source.get_ohlcv(symbol, start_str, end_str, interval="1D")
        if df is None or df.empty:
            raise ValueError("empty data")
        df = df.copy()
        df["time"] = pd.to_datetime(df["time"])
        close = df.set_index("time").sort_index()["close"].reindex(all_dates, method="ffill")
        close = close.dropna()
        if close.empty:
            raise ValueError("no valid closes after reindex")
        return close / close.iloc[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Benchmark [{symbol}] unavailable: {exc}; will use fallback.")
        return pd.Series(dtype=float)


def build_equal_weight_curve(
    all_ohlcv: Dict[str, pd.DataFrame],
    tickers: List[str],
    all_dates: pd.DatetimeIndex,
) -> pd.Series:
    """Equal-weight buy-and-hold curve as benchmark fallback (normalised, start=1.0)."""
    curves = []
    for ticker in tickers:
        df = all_ohlcv.get(ticker, pd.DataFrame())
        if df.empty:
            continue
        df = df.copy()
        df["time"] = pd.to_datetime(df["time"])
        close = df.set_index("time")["close"].reindex(all_dates, method="ffill")
        valid = close.dropna()
        if valid.empty:
            continue
        curves.append(close / valid.iloc[0])
    if not curves:
        return pd.Series(1.0, index=all_dates)
    combined = pd.concat(curves, axis=1).mean(axis=1).ffill()
    return combined / combined.iloc[0]


_FREQ_MONTHS = {"monthly": 1, "quarterly": 3, "semiannual": 6, "annual": 12}


def rebalance_dates(start: date, end: date, freq: str) -> List[date]:
    """Generate rebalance date list within [start, end].

    freq: monthly (1m) | quarterly (3m) | semiannual (6m) | annual (12m).
    Lower frequency = fewer round-trips = less fee drag.
    """
    step = _FREQ_MONTHS.get(freq)
    if step is None:
        raise ValueError(f"Unknown rebalance_freq: {freq!r}. Use {list(_FREQ_MONTHS)}.")
    result: List[date] = []
    current = start
    while current <= end:
        result.append(current)
        m = current.month + step
        y = current.year + (m - 1) // 12
        current = date(y, ((m - 1) % 12) + 1, 1)
    return result
