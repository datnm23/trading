"""VN stock universe definitions.

Provides get_universe(name) returning a list of ticker strings.
Config override: system.yaml data_vn.universe.{name} key.

VN30 list verified 2026-06-15 via Listing(source='VCI').symbols_by_group('VN30').
"""

import os
from typing import Dict, List, Optional

from loguru import logger

# VN30 universe as of 2026-06-15
_VN30: List[str] = [
    "ACB", "BID", "BSR", "CTG", "FPT",
    "GAS", "GVR", "HDB", "HPG", "LPB",
    "MBB", "MSN", "MWG", "PLX", "SAB",
    "SHB", "SSB", "SSI", "STB", "TCB",
    "TPB", "VCB", "VHM", "VIB", "VIC",
    "VJC", "VNM", "VPB", "VPL", "VRE",
]

# Known banks in VN30 (from is_bank flag in company.overview)
_VN30_BANKS: frozenset = frozenset([
    "ACB", "BID", "CTG", "HDB", "LPB",
    "MBB", "SHB", "SSB", "STB", "TCB",
    "TPB", "VCB", "VIB", "VPB",
])

_REGISTRY: Dict[str, List[str]] = {
    "VN30": _VN30,
}

# Static VN30 company metadata: ticker -> (short_name, sector).
# Used for display + relative-valuation peer grouping WITHOUT live vnstock calls
# (which rate-limit/hard-terminate). Names/sectors are stable for VN30.
_VN30_META: Dict[str, tuple] = {
    "ACB": ("Ngân hàng Á Châu", "Ngân hàng"),
    "BID": ("BIDV", "Ngân hàng"),
    "BSR": ("Lọc hóa dầu Bình Sơn", "Dầu khí"),
    "CTG": ("VietinBank", "Ngân hàng"),
    "FPT": ("Tập đoàn FPT", "Công nghệ"),
    "GAS": ("PV GAS", "Dầu khí"),
    "GVR": ("Cao su Việt Nam", "Cao su"),
    "HDB": ("HDBank", "Ngân hàng"),
    "HPG": ("Hòa Phát", "Thép"),
    "LPB": ("LPBank", "Ngân hàng"),
    "MBB": ("MB Bank", "Ngân hàng"),
    "MSN": ("Masan Group", "Tiêu dùng - Bán lẻ"),
    "MWG": ("Thế Giới Di Động", "Bán lẻ"),
    "PLX": ("Petrolimex", "Dầu khí"),
    "SAB": ("Sabeco", "Đồ uống"),
    "SHB": ("Ngân hàng SHB", "Ngân hàng"),
    "SSB": ("SeABank", "Ngân hàng"),
    "SSI": ("Chứng khoán SSI", "Chứng khoán"),
    "STB": ("Sacombank", "Ngân hàng"),
    "TCB": ("Techcombank", "Ngân hàng"),
    "TPB": ("TPBank", "Ngân hàng"),
    "VCB": ("Vietcombank", "Ngân hàng"),
    "VHM": ("Vinhomes", "Bất động sản"),
    "VIB": ("Ngân hàng VIB", "Ngân hàng"),
    "VIC": ("Vingroup", "Bất động sản - Đa ngành"),
    "VJC": ("Vietjet Air", "Hàng không"),
    "VNM": ("Vinamilk", "Thực phẩm"),
    "VPB": ("VPBank", "Ngân hàng"),
    "VPL": ("Vinpearl", "Du lịch - Nghỉ dưỡng"),
    "VRE": ("Vincom Retail", "Bất động sản bán lẻ"),
}


def get_universe(name: str, config_override: Optional[Dict] = None) -> List[str]:
    """Return list of tickers for the named universe.

    Args:
        name: Universe name, e.g. 'VN30'.
        config_override: Optional dict from system.yaml data_vn.universe section.
                         If it contains key `name`, that list is used instead.

    Returns:
        List of ticker strings.

    Raises:
        ValueError: If universe name is unknown and no config override.
    """
    if config_override and name in config_override:
        tickers = config_override[name]
        logger.debug(f"Universe {name!r} loaded from config override ({len(tickers)} tickers)")
        return list(tickers)

    if name in _REGISTRY:
        tickers = _REGISTRY[name]
        logger.debug(f"Universe {name!r} loaded from built-in registry ({len(tickers)} tickers)")
        return list(tickers)

    raise ValueError(f"Unknown universe: {name!r}. Available: {list(_REGISTRY.keys())}")


def is_bank(ticker: str) -> bool:
    """Return True if ticker is a known bank in VN30.

    This is a static lookup. For live data, use CompanyInfo.is_bank from company.overview.
    """
    return ticker.upper() in _VN30_BANKS


def get_vn30() -> List[str]:
    """Convenience shortcut for get_universe('VN30')."""
    return get_universe("VN30")


def get_company_meta(ticker: str) -> tuple:
    """Return (short_name, sector) for a VN30 ticker from static metadata.

    Falls back to (ticker, "") for unknown tickers. Static lookup — no live
    vnstock call (those rate-limit / hard-terminate the process).
    """
    return _VN30_META.get(ticker.upper(), (ticker.upper(), ""))
