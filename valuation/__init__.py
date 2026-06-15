"""valuation — deterministic per-stock valuation engine for VN stocks.

Public API:
    ValuationResult  — full result dataclass
    recommend()      — run full pipeline: DCF + relative + quality → result
"""

from valuation.recommender import ValuationResult, recommend

__all__ = ["ValuationResult", "recommend"]
