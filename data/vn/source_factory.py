"""Canonical VN data-source factory — single place to wire the data backbone.

Default source = DNSE adjusted OHLCV + vnstock fundamentals, cached:
    CachedDataSource( DnseSource(financial_fallback=VnstockSource()) )

Rationale: DNSE chart-api gives split/dividend-ADJUSTED OHLCV with no guest
rate-limit (fixes screener/backtest price integrity); vnstock supplies the
financial statements/ratios DNSE does not serve. Swap the backbone here only.
"""
from __future__ import annotations

from typing import Optional

from data.vn.base import StockDataSource
from data.vn.cache import CachedDataSource
from data.vn.db_fundamentals_source import DbFundamentalsSource
from data.vn.dnse_source import DnseSource
from data.vn.vnstock_source import VnstockSource


def build_default_source(
    cache_dir: str = "./data/vn_cache",
    db_url: Optional[str] = None,
    vnstock_throttle: float = 5.0,
) -> StockDataSource:
    """Build the canonical cached hybrid source (DNSE prices + vnstock fundamentals).

    Used by the offline collector and backtest. NOT for the live backend — vnstock
    rate-limits at request time; use build_advisory_source() there instead.
    """
    fundamentals = VnstockSource(source="VCI", throttle_seconds=vnstock_throttle)
    hybrid = DnseSource(financial_fallback=fundamentals)
    return CachedDataSource(hybrid, cache_dir=cache_dir, db_url=db_url)


def build_advisory_source(
    cache_dir: str = "./data/vn_cache",
    db_url: Optional[str] = None,
) -> StockDataSource:
    """Build the live-backend source: DNSE prices + DB fundamentals (no live vnstock).

    Prices come from DNSE chart-api (cached parquet, no rate-limit); financials,
    ratios and company info are served from the DB (vn_financials, pre-collected).
    Eliminates the 61s stock-detail load and the 500 on valuation caused by live
    vnstock peer fan-out.
    """
    # Longer OHLCV TTL (6h) than the 15-min default: advisory prices are EOD-grade,
    # and a long TTL keeps the valuation peer fan-out (~29 VN30 closes) served from
    # the parquet cache instead of re-fetching DNSE on every request.
    prices = CachedDataSource(
        DnseSource(), cache_dir=cache_dir, db_url=db_url, ttl={"ohlcv": 21_600}
    )
    return DbFundamentalsSource(price_source=prices)
