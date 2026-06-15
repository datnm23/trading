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
