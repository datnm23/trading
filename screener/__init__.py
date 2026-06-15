"""screener — config-driven FA+TA screener for VN Stock Advisory.

Public API:
    ScreenerEngine   — main entry point
    WatchlistItem    — output item (ticker, score, rank, criteria breakdown)
    CriterionResult  — per-criterion result (key, label, passed, value, weight)
"""

from screener.engine import ScreenerEngine
from screener.scorer import CriterionResult, WatchlistItem

__all__ = ["ScreenerEngine", "WatchlistItem", "CriterionResult"]
