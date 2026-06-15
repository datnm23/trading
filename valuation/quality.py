"""Quality scoring: Piotroski F-score (9 criteria) and Altman Z-score.

Banks: Altman Z not applicable (no current_assets/current_liabilities).
Banks also structurally lack F5 (long_term_borrowings) and F8 (net_sales/gross_profit);
those criteria are excluded from `f_score_applicable` so the normalized fraction
`f_score_pct` is comparable across bank vs non-bank.
All scores degrade gracefully — missing items counted as 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo

# Criteria that are structurally inapplicable for banks
_BANK_NA_CRITERIA = frozenset({"F5_leverage_decreasing", "F8_gross_margin_improving"})


@dataclass
class QualityResult:
    ticker: str
    f_score: Optional[int]           # raw integer: sum of passed criteria (0-9)
    f_score_applicable: int          # count of criteria evaluated (≤ 9; 7 for banks)
    f_score_pct: Optional[float]     # passed / applicable — 0..1, comparable across types
    f_score_details: dict             # criterion_name -> 0|1
    z_score: Optional[float]         # None for banks or missing data
    z_score_applicable: bool
    z_interpretation: str            # "safe" | "grey" | "distress" | "n/a"
    notes: list[str] = field(default_factory=list)


def _lv(items: dict, key: str) -> Optional[float]:
    """Most recent non-None value for key."""
    for label in sorted(items.get(key, {}).keys(), reverse=True):
        v = items[key][label]
        if v is not None:
            return float(v)
    return None


def _lv2(items: dict, key: str) -> tuple[Optional[float], Optional[float]]:
    """(latest, prior-year) for key."""
    labels = sorted(items.get(key, {}).keys(), reverse=True)
    get = lambda i: float(items[key][labels[i]]) if i < len(labels) else None  # noqa: E731
    return get(0), get(1)


def _f_binary(cond: Optional[bool]) -> int:
    return 1 if cond else 0


def _piotroski(bs: dict, inc: dict, cf: dict, ratios: dict) -> tuple[int, dict]:
    """Return (total_f_score 0-9, detail_dict) with 9 binary Piotroski criteria."""
    d: dict[str, int] = {}

    # ── Profitability ──────────────────────────────────────────────────────
    ta_now, ta_prev = _lv2(bs, "total_assets")
    ni_now, ni_prev = _lv2(inc, "net_profit_loss_after_tax")
    avg_ta = (ta_now + ta_prev) / 2 if ta_now and ta_prev else ta_now

    roa_now = ni_now / avg_ta if ni_now is not None and avg_ta else None
    d["F1_roa_positive"] = _f_binary(roa_now is not None and roa_now > 0)

    cfo = _lv(cf, "net_cash_inflows_outflows_from_operating_activities")
    d["F2_cfo_positive"] = _f_binary(cfo is not None and cfo > 0)

    # ROA YoY: need prior-period TA for prior avg_ta
    ta_labels = sorted(bs.get("total_assets", {}).keys(), reverse=True)
    ta_prior_prev = float(bs["total_assets"][ta_labels[2]]) if len(ta_labels) >= 3 else None
    avg_ta_prev = (ta_prev + ta_prior_prev) / 2 if ta_prev and ta_prior_prev else ta_prev
    roa_prev = ni_prev / avg_ta_prev if ni_prev is not None and avg_ta_prev else None
    d["F3_roa_increasing"] = _f_binary(
        roa_now is not None and roa_prev is not None and roa_now > roa_prev
    )

    # Accrual quality: CFO/TA > ROA
    cfo_ratio = cfo / avg_ta if cfo is not None and avg_ta else None
    d["F4_accrual_quality"] = _f_binary(
        cfo_ratio is not None and roa_now is not None and cfo_ratio > roa_now
    )

    # ── Leverage / Liquidity ───────────────────────────────────────────────
    ltd_now, ltd_prev = _lv2(bs, "long_term_borrowings")
    lev_now = ltd_now / ta_now if ltd_now is not None and ta_now else None
    lev_prev = ltd_prev / ta_prev if ltd_prev is not None and ta_prev else None
    d["F5_leverage_decreasing"] = _f_binary(
        lev_now is not None and lev_prev is not None and lev_now < lev_prev
    )

    cr_now, cr_prev = _lv2(ratios, "current_ratio")
    d["F6_current_ratio_improving"] = _f_binary(
        cr_now is not None and cr_prev is not None and cr_now > cr_prev
    )

    sh_now, sh_prev = _lv2(ratios, "outstanding_shares")
    d["F7_no_dilution"] = _f_binary(
        sh_now is not None and sh_prev is not None and sh_prev > 0 and sh_now <= sh_prev * 1.01
    )

    # ── Operating Efficiency ───────────────────────────────────────────────
    gp_now, gp_prev = _lv2(inc, "gross_profit")
    rev_now, rev_prev = _lv2(inc, "net_sales")
    gm_now = gp_now / rev_now if gp_now is not None and rev_now else None
    gm_prev = gp_prev / rev_prev if gp_prev is not None and rev_prev else None
    d["F8_gross_margin_improving"] = _f_binary(
        gm_now is not None and gm_prev is not None and gm_now > gm_prev
    )

    at_now, at_prev = _lv2(ratios, "asset_turnover")
    d["F9_asset_turnover_improving"] = _f_binary(
        at_now is not None and at_prev is not None and at_now > at_prev
    )

    return sum(d.values()), d


def _altman_z(bs: dict, inc: dict, total_liabilities: Optional[float]) -> Optional[float]:
    """Altman Z′ (private-firm / book-equity variant).

    Formula: Z′ = 0.717·X1 + 0.847·X2 + 3.107·X3 + 0.420·X4 + 0.998·X5
      X4 = book equity / total liabilities  (NOT market cap — this is Z′, not Z)
    Bands: > 2.9 safe, 1.23–2.9 grey, < 1.23 distress.
    Returns None if total_assets missing (required denominator).
    """
    ta = _lv(bs, "total_assets")
    if not ta:
        return None
    ca, cl = _lv(bs, "current_assets") or 0, _lv(bs, "current_liabilities") or 0
    re = _lv(bs, "undistributed_earnings") or 0
    oe = _lv(bs, "owners_equity") or 0
    ebit = _lv(inc, "operating_profit_loss") or 0
    sales = (_lv(inc, "net_sales") or _lv(inc, "sales") or 0)
    liab = total_liabilities or _lv(bs, "liabilities") or 1.0

    x1, x2, x3 = (ca - cl) / ta, re / ta, ebit / ta
    x4 = oe / liab if liab else 0.0
    x5 = sales / ta
    return round(0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5, 3)


def _z_interp(z: Optional[float], applicable: bool) -> str:
    if not applicable or z is None:
        return "n/a"
    if z > 2.9:
        return "safe"
    if z > 1.23:
        return "grey"
    return "distress"


def run_quality(
    ticker: str,
    src: StockDataSource,
    company: Optional[CompanyInfo] = None,
) -> QualityResult:
    """Compute Piotroski F-score (normalized for banks) and Altman Z′. Never raises."""
    if company is None:
        company = src.get_company(ticker)

    is_bank = company.is_bank if company else False

    bs = src.get_financials(ticker, "balance_sheet", period="year")
    inc = src.get_financials(ticker, "income_statement", period="year")
    cf = src.get_financials(ticker, "cash_flow", period="year")
    ratios = src.get_ratios(ticker, period="year")

    f_total, f_details = _piotroski(bs.items, inc.items, cf.items, ratios.items)

    # For banks, F5 and F8 are structurally inapplicable — exclude from denominator
    # so the normalized fraction is comparable across bank vs non-bank.
    if is_bank:
        applicable_keys = [k for k in f_details if k not in _BANK_NA_CRITERIA]
    else:
        applicable_keys = list(f_details.keys())

    f_score_applicable = len(applicable_keys)
    passed_applicable = sum(f_details[k] for k in applicable_keys)
    f_score_pct = passed_applicable / f_score_applicable if f_score_applicable > 0 else None

    z_applicable = not is_bank
    z_score: Optional[float] = None

    if is_bank:
        f_note = (
            f"F-score {passed_applicable}/{f_score_applicable} (áp dụng, "
            f"{len(_BANK_NA_CRITERIA)} tiêu chí không áp dụng với ngân hàng)"
        )
    else:
        f_note = f"F-score: {f_total}/9"
    notes = [f_note]

    if z_applicable:
        liab = _lv(bs.items, "liabilities")
        z_score = _altman_z(bs.items, inc.items, liab)
        notes.append(f"Altman Z': {z_score:.2f}" if z_score is not None else "Thiếu dữ liệu BS để tính Altman Z")
    else:
        notes.append("Bank: Altman Z-score không áp dụng")

    logger.debug(f"{ticker}: F-score={f_total}/{f_score_applicable} ({f_score_pct:.0%}), Z={z_score} ({_z_interp(z_score, z_applicable)})")
    return QualityResult(
        ticker=ticker, f_score=f_total, f_score_applicable=f_score_applicable,
        f_score_pct=f_score_pct, f_score_details=f_details,
        z_score=z_score, z_score_applicable=z_applicable,
        z_interpretation=_z_interp(z_score, z_applicable), notes=notes,
    )
