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
from data.vn.dnse_source import DnseSource
from data.vn.vnstock_source import VnstockSource


def build_default_source(
    cache_dir: str = "./data/vn_cache",
    db_url: Optional[str] = None,
    vnstock_throttle: float = 5.0,
) -> StockDataSource:
    """Build the project's canonical cached hybrid source (DNSE + vnstock)."""
    fundamentals = VnstockSource(source="VCI", throttle_seconds=vnstock_throttle)
    hybrid = DnseSource(financial_fallback=fundamentals)
    return CachedDataSource(hybrid, cache_dir=cache_dir, db_url=db_url)
