"""DCF valuation model for non-bank VN stocks.

FCFF = net_cash_inflows_outflows_from_operating_activities - |purchases_of_fixed_assets...|
Banks: DCF classic invalid → dcf_applicable=False, returns None intrinsic value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import yaml
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo


def _load_cfg() -> dict:
    try:
        with open("config/valuation.yaml") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config/valuation.yaml: {e}; using defaults")
        return {}


@dataclass
class DcfResult:
    ticker: str
    dcf_applicable: bool
    intrinsic_value: Optional[float]        # VND per share
    fcff_ttm: Optional[float]               # trailing FCFF (absolute VND)
    growth_rate: Optional[float]
    wacc: float
    terminal_growth: float
    sensitivity: dict = field(default_factory=dict)  # {(wacc, g): intrinsic_value}
    notes: list[str] = field(default_factory=list)


def _latest_value(items: dict, key: str) -> Optional[float]:
    """Return the most recent non-None float for key in financial items dict."""
    period_vals = items.get(key, {})
    for label in sorted(period_vals.keys(), reverse=True):
        v = period_vals[label]
        if v is not None:
            return float(v)
    return None


def _get_shares(company: CompanyInfo, ratios_items: dict) -> Optional[float]:
    """Outstanding shares: prefer ratios, fallback company.issue_share."""
    shares = _latest_value(ratios_items, "outstanding_shares")
    if shares and shares > 0:
        return shares
    if company.issue_share and company.issue_share > 0:
        return company.issue_share
    return None


def _compute_fcff(cf_items: dict) -> Optional[float]:
    """FCFF = operating_cfo - |capex| for non-bank."""
    cfo = _latest_value(cf_items, "net_cash_inflows_outflows_from_operating_activities")
    capex = _latest_value(cf_items, "purchases_of_fixed_assets_and_other_long_term_assets")
    if cfo is None:
        return None
    return cfo - abs(capex) if capex is not None else cfo


def _dcf_value(fcff: float, growth: float, wacc: float, terminal_growth: float, years: int) -> float:
    """Compute DCF intrinsic firm value (absolute VND)."""
    if wacc <= terminal_growth:
        raise ValueError(f"WACC ({wacc}) must exceed terminal_growth ({terminal_growth})")
    pv, cf = 0.0, fcff
    for t in range(1, years + 1):
        cf *= 1 + growth
        pv += cf / (1 + wacc) ** t
    tv = cf * (1 + terminal_growth) / (wacc - terminal_growth)
    return pv + tv / (1 + wacc) ** years


def _infer_growth(cf_items: dict) -> float:
    """Estimate FCF growth from 2-yr CAGR of operating cash flows; default 8%."""
    vals = cf_items.get("net_cash_inflows_outflows_from_operating_activities", {})
    labels = sorted(vals.keys(), reverse=True)
    if len(labels) >= 3:
        newest, oldest = vals.get(labels[0]), vals.get(labels[2])
        if newest and oldest and oldest > 0:
            return max(-0.05, min(0.30, (newest / oldest) ** 0.5 - 1))
    return 0.08


def _early_exit(ticker: str, wacc: float, tg: float, applicable: bool, note: str, fcff=None) -> DcfResult:
    return DcfResult(ticker=ticker, dcf_applicable=applicable, intrinsic_value=None,
                     fcff_ttm=fcff, growth_rate=None, wacc=wacc, terminal_growth=tg, notes=[note])


def run_dcf(
    ticker: str,
    src: StockDataSource,
    company: Optional[CompanyInfo] = None,
    cfg: Optional[dict] = None,
) -> DcfResult:
    """Compute DCF intrinsic value. Returns dcf_applicable=False for banks. Never raises."""
    if cfg is None:
        cfg = _load_cfg()
    dcf_cfg = cfg.get("dcf", {})
    wacc = dcf_cfg.get("wacc", 0.13)
    tg = dcf_cfg.get("terminal_growth", 0.03)
    years = dcf_cfg.get("projection_years", 5)

    if company is None:
        company = src.get_company(ticker)

    if company and company.is_bank:
        return _early_exit(ticker, wacc, tg, False, "Bank: DCF classic không áp dụng, dùng relative+quality")

    cf = src.get_financials(ticker, "cash_flow", period="year")
    fcff = _compute_fcff(cf.items)

    if fcff is None:
        return _early_exit(ticker, wacc, tg, True, "Thiếu dữ liệu cash flow, không tính được DCF")
    if fcff <= 0:
        return _early_exit(ticker, wacc, tg, True, f"FCFF âm ({fcff/1e9:.1f} tỷ), DCF không đáng tin cậy", fcff)

    ratios = src.get_ratios(ticker, period="year")
    shares = _get_shares(company, ratios.items) if company else None
    if not shares or shares <= 0:
        return _early_exit(ticker, wacc, tg, True, "Thiếu số lượng cổ phiếu lưu hành", fcff)

    growth = _infer_growth(cf.items)
    try:
        firm_value = _dcf_value(fcff, growth, wacc, tg, years)
    except ValueError as e:
        return _early_exit(ticker, wacc, tg, True, f"Lỗi tính DCF: {e}", fcff)

    intrinsic = firm_value / shares

    # Sensitivity grid: WACC ± 1%, terminal_growth ± 0.5%
    sensitivity: dict = {}
    for dw in (-0.01, 0.0, 0.01):
        for dg in (-0.005, 0.0, 0.005):
            w2, g2 = round(wacc + dw, 4), round(tg + dg, 4)
            if w2 > g2:
                try:
                    sensitivity[(w2, g2)] = round(_dcf_value(fcff, growth, w2, g2, years) / shares, 0)
                except Exception:
                    pass

    logger.debug(f"{ticker}: DCF intrinsic={intrinsic:.0f} VND/share, growth={growth:.1%}")
    return DcfResult(
        ticker=ticker, dcf_applicable=True, intrinsic_value=intrinsic,
        fcff_ttm=fcff, growth_rate=growth, wacc=wacc, terminal_growth=tg,
        sensitivity=sensitivity,
        notes=[
            f"FCFF TTM: {fcff/1e9:.1f} tỷ VND",
            f"Tăng trưởng ước tính: {growth:.1%}",
            f"WACC: {wacc:.1%}, terminal growth: {tg:.1%}",
        ],
    )
