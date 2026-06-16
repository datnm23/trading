"""DNSE LightSpeed OHLCV adapter — historical price via public chart-api.

Why: vnstock guest tier rate-limits (20 req/min) and serves UNADJUSTED prices,
which corrupted the screener backtest. DNSE's chart-api is public (no auth),
has no guest rate-limit, and returns split/dividend-ADJUSTED OHLCV — fixing
backtest price integrity.

Endpoint (verified 2026-06-16, no auth required):
    GET https://api.dnse.com.vn/chart-api/v2/ohlcs/{asset}
        ?symbol=HPG&resolution=1D&from={unix_s}&to={unix_s}
    → {"t":[...],"o":[...],"h":[...],"l":[...],"c":[...],"v":[...],"nextTime":0}
    asset = "stock" for equities, "index" for VNINDEX/VN30/HNX... indices.
    Prices already in THOUSANDS of VND (matches StockDataSource contract).

DNSE does NOT serve fundamentals (financials/ratios/company). Those are
delegated to a fallback StockDataSource (e.g. VnstockSource) via composition —
giving a hybrid: DNSE adjusted prices + vnstock fundamentals.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios

_CHART_URL = "https://api.dnse.com.vn/chart-api/v2/ohlcs/{asset}"

# Symbols served under the "index" asset path (not "stock").
_INDEX_SYMBOLS = {
    "VNINDEX", "VN30", "VN100", "VNALLSHARE",
    "HNXINDEX", "HNX30", "UPCOMINDEX",
}

# Map our interval labels → DNSE resolution tokens (1,3,5,15,30,1H,1D,1W).
_RESOLUTION_MAP = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
    "1H": "1H", "1h": "1H", "1D": "1D", "D": "1D", "1W": "1W", "W": "1W",
}

_OHLCV_COLS = ["time", "open", "high", "low", "close", "volume"]


class DnseSource(StockDataSource):
    """DNSE chart-api OHLCV source; fundamentals delegated to a fallback source."""

    def __init__(
        self,
        financial_fallback: Optional[StockDataSource] = None,
        timeout: int = 15,
    ):
        """
        Args:
            financial_fallback: source used for financials/ratios/company
                (DNSE serves none). e.g. VnstockSource(). If None, those calls raise.
            timeout: HTTP timeout seconds.
        """
        self.fallback = financial_fallback
        self.timeout = timeout

    # ------------------------------------------------------------------
    # OHLCV — DNSE chart-api (no auth)
    # ------------------------------------------------------------------
    def get_ohlcv(
        self, ticker: str, start: str, end: str, interval: str = "1D"
    ) -> pd.DataFrame:
        """Fetch adjusted OHLCV. Prices in THOUSANDS of VND. Empty df on failure."""
        symbol = ticker.upper()
        asset = "index" if symbol in _INDEX_SYMBOLS else "stock"
        resolution = _RESOLUTION_MAP.get(interval, "1D")
        try:
            frm = self._to_unix(start)
            # +1 day so the end date itself is inclusive.
            to = self._to_unix(end) + 86_400
            resp = requests.get(
                _CHART_URL.format(asset=asset),
                params={"symbol": symbol, "resolution": resolution, "from": frm, "to": to},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("t"):
                logger.warning(f"DNSE OHLCV empty for {symbol} [{start}..{end}]")
                return pd.DataFrame(columns=_OHLCV_COLS)
            df = pd.DataFrame(
                {
                    # Floor to midnight so daily bars are date-keyed (00:00:00),
                    # matching vnstock's format. DNSE unix ts carry a time-of-day
                    # (~02:00 UTC) that otherwise breaks as-of clipping & date slicing.
                    "time": pd.to_datetime(data["t"], unit="s").normalize(),
                    "open": data["o"],
                    "high": data["h"],
                    "low": data["l"],
                    "close": data["c"],
                    "volume": data["v"],
                }
            )
            return df.sort_values("time").reset_index(drop=True)
        except Exception as exc:  # noqa: BLE001 — degrade gracefully per contract
            logger.error(f"DNSE OHLCV fetch failed for {symbol}: {exc}")
            return pd.DataFrame(columns=_OHLCV_COLS)

    @staticmethod
    def _to_unix(date_str: str) -> int:
        """ISO date/datetime → UTC unix seconds. Accepts 'YYYY-MM-DD'."""
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())

    # ------------------------------------------------------------------
    # Fundamentals — delegated to fallback (DNSE serves none)
    # ------------------------------------------------------------------
    def _fallback(self, kind: str) -> StockDataSource:
        if self.fallback is None:
            raise NotImplementedError(
                f"DNSE does not serve {kind}; pass financial_fallback=VnstockSource()"
            )
        return self.fallback

    def get_financials(
        self, ticker: str, statement_type: str, period: str = "year"
    ) -> FinancialStatement:
        return self._fallback("financials").get_financials(ticker, statement_type, period)

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        return self._fallback("ratios").get_ratios(ticker, period)

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        return self._fallback("company").get_company(ticker)
