"""Composite scorer: normalise per-criterion values → weighted score 0..100.

Design:
- Each criterion produces (passed, value, label). value=None → N/A, excluded.
- Normalisation: min-max across all tickers for that criterion.
- N/A criteria are excluded from both numerator and denominator (not penalised).
- Final score = sum(normalised_value * weight) / sum(active_weights) * 100.
- Ranking: descending by score; ties broken alphabetically by ticker.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from loguru import logger


@dataclass
class CriterionResult:
    """Single criterion outcome for one ticker."""
    key: str          # internal key e.g. "roe"
    label: str        # human-readable label
    passed: bool
    value: Optional[float]   # None = N/A (missing data)
    weight: float


@dataclass
class WatchlistItem:
    """Screener output for one ticker."""
    ticker: str
    score: float                           # 0..100 composite
    rank: int                              # 1 = best
    criteria: List[CriterionResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.criteria if c.passed)

    @property
    def na_count(self) -> int:
        return sum(1 for c in self.criteria if c.value is None)

    def breakdown(self) -> List[Tuple[str, bool, Optional[float]]]:
        """Returns list of (label, passed, value) for display."""
        return [(c.label, c.passed, c.value) for c in self.criteria]


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _normalise_values(
    raw: Dict[str, Optional[float]],
) -> Dict[str, Optional[float]]:
    """Min-max normalise a dict of ticker → value (None entries excluded).

    Returns dict with same keys; N/A entries preserved as None.
    When all values are identical, returns 0.5 for all (avoid division by zero).
    """
    valid = {k: v for k, v in raw.items() if v is not None}
    if not valid:
        return {k: None for k in raw}

    lo, hi = min(valid.values()), max(valid.values())
    result: Dict[str, Optional[float]] = {}
    for k, v in raw.items():
        if v is None:
            result[k] = None
        elif hi == lo:
            result[k] = 0.5
        else:
            result[k] = (v - lo) / (hi - lo)
    return result


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def compute_scores(
    per_ticker_criteria: Dict[str, List[CriterionResult]],
) -> Dict[str, float]:
    """Compute composite score 0..100 for each ticker.

    Args:
        per_ticker_criteria: {ticker: [CriterionResult, ...]}

    Returns:
        {ticker: score}
    """
    # Collect all unique criterion keys preserving insertion order
    all_keys: List[str] = []
    seen: set = set()
    for criteria in per_ticker_criteria.values():
        for c in criteria:
            if c.key not in seen:
                all_keys.append(c.key)
                seen.add(c.key)

    # Per criterion: gather raw values across tickers, normalise
    normalised: Dict[str, Dict[str, Optional[float]]] = {}
    weights: Dict[str, float] = {}

    for key in all_keys:
        raw: Dict[str, Optional[float]] = {}
        w = 0.0
        for ticker, criteria in per_ticker_criteria.items():
            match = next((c for c in criteria if c.key == key), None)
            if match is not None:
                raw[ticker] = match.value
                w = match.weight  # same weight for same key across tickers
        normalised[key] = _normalise_values(raw)
        weights[key] = w

    # Compute weighted sum per ticker
    scores: Dict[str, float] = {}
    for ticker, criteria in per_ticker_criteria.items():
        total_w = 0.0
        weighted_sum = 0.0
        for key in all_keys:
            norm_val = normalised.get(key, {}).get(ticker)
            if norm_val is None:
                continue  # N/A — exclude from score
            w = weights[key]
            weighted_sum += norm_val * w
            total_w += w

        score = (weighted_sum / total_w * 100.0) if total_w > 0 else 0.0
        scores[ticker] = round(score, 2)
        logger.debug(f"[{ticker}] score={score:.2f} total_weight={total_w:.2f}")

    return scores


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def rank_watchlist(
    per_ticker_criteria: Dict[str, List[CriterionResult]],
) -> List[WatchlistItem]:
    """Compute scores, rank descending, return ordered WatchlistItem list."""
    scores = compute_scores(per_ticker_criteria)

    items: List[WatchlistItem] = []
    for ticker, criteria in per_ticker_criteria.items():
        items.append(WatchlistItem(
            ticker=ticker,
            score=scores.get(ticker, 0.0),
            rank=0,  # assigned below
            criteria=criteria,
        ))

    # Sort: descending score, ties broken alphabetically
    items.sort(key=lambda x: (-x.score, x.ticker))
    for i, item in enumerate(items, start=1):
        item.rank = i

    return items
