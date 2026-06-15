"""FA filter functions for VN Stock screener.

Each filter is a pure function returning (passed: bool, value: float | None, label: str).
value=None signals N/A (missing data) — engine excludes from score normalization.
Bank branches are handled per vnstock-field-reference.md conventions.
"""

import math
from typing import Optional, Tuple
from loguru import logger

from data.vn.models import FinancialStatement, Ratios, CompanyInfo

FilterResult = Tuple[bool, Optional[float], str]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _latest_ratio(ratios: Ratios, key: str) -> Optional[float]:
    """Return the most recent available value for a ratio key.

    period_labels may be messy/duplicated (per field reference warning).
    Strategy: scan all period→value entries and return the one whose label
    sorts last lexicographically (YYYYqQ format sorts correctly by year/quarter).
    """
    data = ratios.items.get(key)
    if not data:
        return None
    # 0.0 is a legitimate value (e.g. zero-debt D/E=0.0 is a strong pass).
    # Exclude only non-numeric and NaN — not falsiness.
    numeric = {k: v for k, v in data.items()
               if isinstance(v, (int, float)) and not math.isnan(v)}
    if not numeric:
        return None
    latest_label = max(numeric.keys())
    return numeric[latest_label]


def _latest_financials(stmt: FinancialStatement, item_id: str) -> Optional[float]:
    """Return the most recent available value for a financial statement item."""
    data = stmt.items.get(item_id)
    if not data:
        return None
    numeric = {k: v for k, v in data.items() if isinstance(v, (int, float))}
    if not numeric:
        return None
    return numeric[max(numeric.keys())]


def _prior_year_financials(stmt: FinancialStatement, item_id: str) -> Optional[float]:
    """Return the second-most-recent value (prior year) for a financial item."""
    data = stmt.items.get(item_id)
    if not data:
        return None
    numeric = {k: v for k, v in data.items() if isinstance(v, (int, float))}
    if len(numeric) < 2:
        return None
    sorted_labels = sorted(numeric.keys())
    return numeric[sorted_labels[-2]]


# ---------------------------------------------------------------------------
# FA Filters
# ---------------------------------------------------------------------------

def filter_roe(ratios: Ratios, threshold: float) -> FilterResult:
    """ROE > threshold (e.g. 0.15 = 15%)."""
    label = f"ROE > {threshold:.0%}"
    value = _latest_ratio(ratios, "roe")
    if value is None:
        logger.debug(f"[{ratios.ticker}] ROE: N/A (missing data)")
        return False, None, label
    passed = value > threshold
    logger.debug(f"[{ratios.ticker}] ROE={value:.2%} threshold={threshold:.2%} passed={passed}")
    return passed, value, label


def filter_pe_ratio(
    ratios: Ratios,
    threshold: float,
    sector_median: Optional[float],
) -> FilterResult:
    """P/E < threshold AND < sector_median (if available).

    sector_median: pre-computed median P/E for same-sector tickers.
    Falls back to threshold-only check when sector_median is None.
    """
    label = "P/E < threshold & sector median"
    value = _latest_ratio(ratios, "pe_ratio")
    if value is None:
        logger.debug(f"[{ratios.ticker}] P/E: N/A")
        return False, None, label
    # Negative P/E (loss-making) is treated as fail — not meaningful
    if value <= 0:
        return False, value, label
    below_threshold = value < threshold
    below_sector = (value < sector_median) if sector_median is not None else True
    passed = below_threshold and below_sector
    logger.debug(
        f"[{ratios.ticker}] P/E={value:.1f} threshold={threshold} "
        f"sector_median={sector_median} passed={passed}"
    )
    return passed, value, label


def filter_eps_growth(income: FinancialStatement, threshold: float = 0.0) -> FilterResult:
    """EPS growth YoY > threshold.

    Uses eps_basic_vnd (available for both bank and non-bank per field ref).
    Falls back to net_profit_loss_after_tax if EPS missing.
    """
    label = f"EPS YoY > {threshold:.0%}"
    eps_now = _latest_financials(income, "eps_basic_vnd")
    eps_prev = _prior_year_financials(income, "eps_basic_vnd")

    if eps_now is None or eps_prev is None:
        # Fallback: net profit
        eps_now = _latest_financials(income, "net_profit_loss_after_tax")
        eps_prev = _prior_year_financials(income, "net_profit_loss_after_tax")

    if eps_now is None or eps_prev is None or eps_prev == 0:
        logger.debug(f"[{income.ticker}] EPS growth: N/A")
        return False, None, label

    growth = (eps_now - eps_prev) / abs(eps_prev)
    passed = growth > threshold
    logger.debug(f"[{income.ticker}] EPS growth={growth:.2%} passed={passed}")
    return passed, growth, label


def filter_revenue_growth(
    income: FinancialStatement,
    is_bank: bool,
    threshold: float = 0.0,
) -> FilterResult:
    """Revenue growth YoY > threshold.

    Non-bank: net_sales. Bank: total_operating_income (per field reference).
    """
    label = f"Revenue YoY > {threshold:.0%}"
    rev_key = "total_operating_income" if is_bank else "net_sales"
    rev_now = _latest_financials(income, rev_key)
    rev_prev = _prior_year_financials(income, rev_key)

    if rev_now is None or rev_prev is None or rev_prev == 0:
        logger.debug(f"[{income.ticker}] Revenue growth: N/A (key={rev_key})")
        return False, None, label

    growth = (rev_now - rev_prev) / abs(rev_prev)
    passed = growth > threshold
    logger.debug(f"[{income.ticker}] Revenue growth={growth:.2%} passed={passed}")
    return passed, growth, label


def filter_debt_to_equity(
    ratios: Ratios,
    is_bank: bool,
    threshold: float,
) -> FilterResult:
    """D/E < threshold. Skipped (N/A) for banks — leverage is inherent."""
    label = f"D/E < {threshold}"
    if is_bank:
        logger.debug(f"[{ratios.ticker}] D/E: skipped (bank)")
        return True, None, label + " (skipped: bank)"

    value = _latest_ratio(ratios, "debt_to_equity")
    if value is None:
        logger.debug(f"[{ratios.ticker}] D/E: N/A")
        return False, None, label

    passed = value < threshold
    logger.debug(f"[{ratios.ticker}] D/E={value:.2f} threshold={threshold} passed={passed}")
    return passed, value, label


def filter_net_margin(ratios: Ratios, threshold: float) -> FilterResult:
    """Net margin > threshold (e.g. 0.05 = 5%)."""
    label = f"Net margin > {threshold:.0%}"
    value = _latest_ratio(ratios, "net_margin")
    if value is None:
        logger.debug(f"[{ratios.ticker}] Net margin: N/A")
        return False, None, label
    passed = value > threshold
    logger.debug(f"[{ratios.ticker}] Net margin={value:.2%} passed={passed}")
    return passed, value, label
