"""data.vn — VN Stock data adapter package.

Public API:
    StockDataSource  — abstract base (Protocol/ABC)
    VnstockSource    — live data via vnstock 4.x API
    CachedDataSource — TTL-aware caching wrapper
    FinancialStatement, Ratios, CompanyInfo — data models
    get_universe, get_vn30, is_bank — universe helpers
"""

from data.vn.base import StockDataSource
from data.vn.cache import CachedDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from data.vn.universe import get_universe, get_vn30, is_bank
from data.vn.vnstock_source import VnstockSource

__all__ = [
    "StockDataSource",
    "VnstockSource",
    "CachedDataSource",
    "FinancialStatement",
    "Ratios",
    "CompanyInfo",
    "get_universe",
    "get_vn30",
    "is_bank",
]
