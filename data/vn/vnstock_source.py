"""VnstockSource — wraps vnstock 4.x API with throttle + backoff.

OHLCV prices in THOUSANDS of VND (e.g. 48.82 = 48,820đ). Do NOT multiply.
Rate limit: ~20 req/min per IP — prefer sequential batching over concurrent use.
"""

import threading
import time
from typing import Optional

import pandas as pd
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from data.vn.vnstock_parsers import parse_long_financials, parse_ratio_df

_DEFAULT_THROTTLE_S = 3.5
_BACKOFF_WAIT_S = 45.0
_MAX_RETRIES = 2
# Case-insensitive phrases that identify a rate-limit response from VCI/vnstock
_RATE_LIMIT_PHRASES = ("giới hạn", "rate limit", "429", "too many requests")


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True only for known rate-limit signals from vnstock/VCI API."""
    msg = str(exc).lower()
    return any(phrase in msg for phrase in _RATE_LIMIT_PHRASES)


class VnstockSource(StockDataSource):
    """Live data source backed by vnstock 4.x API (VCI source).

    Rate limit: ~20 req/min per IP — prefer sequential batching over concurrent use.

    Args:
        source: Data source identifier (default "VCI" — only source with full financials).
        throttle_seconds: Minimum seconds between API calls (default 3.5).
    """

    _throttle_lock = threading.Lock()  # class-level: safe under multi-threading

    def __init__(self, source: str = "VCI", throttle_seconds: float = _DEFAULT_THROTTLE_S):
        self.source = source
        self.throttle_seconds = throttle_seconds
        self._last_call_ts: float = 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _throttle(self) -> None:
        """Enforce minimum interval between API calls (thread-safe)."""
        with self._throttle_lock:
            elapsed = time.monotonic() - self._last_call_ts
            wait = self.throttle_seconds - elapsed
            if wait > 0:
                time.sleep(wait)
            self._last_call_ts = time.monotonic()

    def _call_with_backoff(self, fn, *args, **kwargs):
        """Call fn(*args, **kwargs) with throttle + exponential backoff on rate-limit.

        Non-rate-limit exceptions propagate immediately without retry.
        Raises RuntimeError if all retries are exhausted on rate-limit errors.
        """
        for attempt in range(_MAX_RETRIES + 1):
            self._throttle()
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                if _is_rate_limit_error(exc) and attempt < _MAX_RETRIES:
                    wait = _BACKOFF_WAIT_S * (2 ** attempt)
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}), "
                        f"backing off {wait:.0f}s: {exc}"
                    )
                    time.sleep(wait)
                    with self._throttle_lock:
                        self._last_call_ts = 0.0  # reset so next _throttle is immediate
                else:
                    raise
        raise RuntimeError("vnstock backoff exhausted: rate limit persists after all retries")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_ohlcv(
        self, ticker: str, start: str, end: str, interval: str = "1D"
    ) -> pd.DataFrame:
        """Fetch OHLCV. Prices in THOUSANDS of VND (vnstock native unit)."""
        from vnstock.api.quote import Quote
        try:
            df = self._call_with_backoff(
                lambda: Quote(symbol=ticker, source=self.source).history(
                    start=start, end=end, interval=interval
                )
            )
            if df is None or df.empty:
                logger.warning(f"OHLCV empty for {ticker}")
                return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
            return df
        except Exception as exc:
            logger.error(f"OHLCV fetch failed for {ticker}: {exc}")
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    def get_financials(
        self, ticker: str, statement_type: str, period: str = "year"
    ) -> FinancialStatement:
        """Fetch and parse financial statement."""
        from vnstock.api.financial import Finance

        _method_map = {
            "balance_sheet": "balance_sheet",
            "income_statement": "income_statement",
            "cash_flow": "cash_flow",
        }
        if statement_type not in _method_map:
            raise ValueError(f"Unknown statement_type: {statement_type!r}")

        empty = FinancialStatement(ticker=ticker, statement_type=statement_type, period=period)
        try:
            fin = Finance(symbol=ticker, source=self.source)
            method = getattr(fin, _method_map[statement_type])
            df = self._call_with_backoff(lambda: method(period=period, lang="vi"))
            return parse_long_financials(df, ticker, statement_type, period)
        except Exception as exc:
            logger.warning(f"Financials ({statement_type}) fetch failed for {ticker}: {exc}")
            return empty

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        """Fetch and parse financial ratios."""
        from vnstock.api.financial import Finance

        empty = Ratios(ticker=ticker, period=period)
        try:
            fin = Finance(symbol=ticker, source=self.source)
            df = self._call_with_backoff(
                lambda: fin.ratio(period=period, lang="vi", dropna=True)
            )
            return parse_ratio_df(df, ticker, period)
        except Exception as exc:
            logger.warning(f"Ratios fetch failed for {ticker}: {exc}")
            return empty

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        """Fetch company overview and map to CompanyInfo."""
        from vnstock.api.company import Company

        try:
            df = self._call_with_backoff(
                lambda: Company(symbol=ticker, source=self.source).overview()
            )
            if df is None or df.empty:
                logger.warning(f"Company overview empty for {ticker}")
                return None

            row = df.iloc[0]

            def _safe(col, default=None):
                """Return scalar value from row, treating NaN/NA as default."""
                val = row.get(col, default)
                # Guard: pd.isna raises on array input — check scalar only
                if not isinstance(val, str):
                    try:
                        if pd.isna(val):
                            return default
                    except (TypeError, ValueError):
                        pass
                return val

            is_bank_raw = _safe("is_bank", 0)
            try:
                is_bank = bool(int(is_bank_raw))
            except (ValueError, TypeError):
                is_bank = str(is_bank_raw).lower() in ("true", "1", "yes")

            icb = _safe("icb_code_lv4") or _safe("icb_code_lv2") or ""

            return CompanyInfo(
                ticker=ticker,
                organ_name=str(_safe("organ_name", "")),
                organ_short_name=str(_safe("organ_short_name", "")),
                sector=str(_safe("sector", "")),
                icb_code=str(icb),
                com_group_code=str(_safe("com_group_code", "")),
                market_cap=float(_safe("market_cap", 0.0) or 0.0),
                current_price=float(_safe("current_price", 0.0) or 0.0),
                issue_share=float(_safe("issue_share", 0.0) or 0.0),
                target_price=_safe("target_price"),
                upside_to_target_pct=_safe("upside_to_target_percent"),
                dividend_per_share_tsr=_safe("dividend_per_share_tsr"),
                free_float_pct=_safe("free_float_percentage"),
                foreigner_pct=_safe("foreigner_percentage"),
                is_bank=is_bank,
                listing_date=str(_safe("listing_date", "")),
            )
        except Exception as exc:
            logger.error(f"Company fetch failed for {ticker}: {exc}")
            return None
