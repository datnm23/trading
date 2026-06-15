"""Blend DCF + relative valuation → target price, score 0-100, BUY/SELL/HOLD, reasons.

Score components (config-weighted):
  upside_weight (50%) + f_score_weight (30%) + z_score_weight (20%, non-bank only)
Banks: z weight redistributed to F-score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import yaml
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo
from valuation.dcf import DcfResult, run_dcf
from valuation.relative import RelativeResult, run_relative
from valuation.quality import QualityResult, run_quality


def _load_cfg() -> dict:
    try:
        with open("config/valuation.yaml") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config/valuation.yaml: {e}; using defaults")
        return {}


@dataclass
class ValuationResult:
    ticker: str
    current_price: float
    intrinsic_value: Optional[float]       # DCF per share (VND)
    target_price: Optional[float]          # blended (VND)
    upside_pct: Optional[float]            # (target - current) / current
    score: int                             # 0-100
    recommendation: str                    # BUY | SELL | HOLD
    f_score: Optional[int]                 # raw passed count (0-9 for non-bank, 0-9 for bank)
    f_score_applicable: int                # criteria evaluated (9 non-bank, 7 bank)
    f_score_pct: Optional[float]           # passed / applicable — 0..1, normalized fraction
    z_score: Optional[float]
    dcf_applicable: bool
    reasons: list[str] = field(default_factory=list)
    disclaimer: str = "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư."
    sensitivity: dict = field(default_factory=dict)


def _blend_target(dcf: DcfResult, rel: RelativeResult, dcf_w: float, rel_w: float) -> Optional[float]:
    """Weighted average of available value estimates; normalises weights."""
    pool: list[tuple[float, float]] = []
    if dcf.dcf_applicable and dcf.intrinsic_value is not None:
        pool.append((dcf.intrinsic_value, dcf_w))
    if rel.implied_value_pe is not None:
        pool.append((rel.implied_value_pe, rel_w))
    if not pool:
        return None
    total_w = sum(w for _, w in pool)
    return sum(v * w / total_w for v, w in pool)


def _upside_score(upside: float, buy: float, sell: float) -> float:
    """Map upside fraction → 0-100 component (monotone)."""
    if upside >= buy:
        return min(100.0, 70.0 + 30.0 * (upside - buy) / max(buy, 1e-9))
    if upside <= sell:
        return max(0.0, 20.0 + 20.0 * (upside - sell) / max(abs(sell), 1e-9))
    return 20.0 + 50.0 * (upside - sell) / (buy - sell)


def _f_component(f_pct: Optional[float]) -> float:
    """Map normalized F-score fraction (0..1) to 0-100 component.

    Uses f_score_pct (passed / applicable) so banks (7 applicable criteria) and
    non-banks (9 applicable criteria) are comparable on the same scale.
    Falls back to 50.0 (neutral) when data is unavailable.
    """
    return f_pct * 100.0 if f_pct is not None else 50.0


def _z_component(z: Optional[float], applicable: bool) -> Optional[float]:
    if not applicable or z is None:
        return None
    if z >= 2.9:
        return min(100.0, 60.0 + 40.0 * (z - 2.9) / 2.0)
    if z <= 1.23:
        return max(0.0, 30.0 * z / 1.23)
    return 30.0 + 30.0 * (z - 1.23) / (2.9 - 1.23)


def _blend_score(up_comp: float, f_comp: float, z_comp: Optional[float], weights: dict) -> int:
    wu = weights.get("upside_weight", 0.50)
    wf = weights.get("f_score_weight", 0.30)
    wz = weights.get("z_score_weight", 0.20) if z_comp is not None else 0.0
    if z_comp is None:
        wf += weights.get("z_score_weight", 0.20)
    total = wu + wf + wz
    score = (up_comp * wu + f_comp * wf + (z_comp or 0) * wz) / total
    return max(0, min(100, round(score)))


def _recommendation(upside: Optional[float], buy: float, sell: float) -> str:
    if upside is None:
        return "HOLD"
    return "BUY" if upside >= buy else ("SELL" if upside <= sell else "HOLD")


def _build_reasons(
    dcf: DcfResult, rel: RelativeResult, quality: QualityResult,
    target: Optional[float], upside: Optional[float], current: float,
) -> list[str]:
    r: list[str] = []
    if target and upside is not None:
        r.append(f"Giá {current/1000:.1f}k → target {target/1000:.1f}k VND (upside {upside*100:+.1f}%)")
    if dcf.dcf_applicable and dcf.intrinsic_value:
        r.append(f"DCF intrinsic: {dcf.intrinsic_value/1000:.1f}k VND/CP (WACC {dcf.wacc:.0%}, g={dcf.terminal_growth:.1%})")
    elif not dcf.dcf_applicable:
        r.append("Ngân hàng: DCF không áp dụng, dùng relative valuation")
    if rel.current_pe and rel.sector_median_pe:
        direction = "thấp hơn" if rel.current_pe < rel.sector_median_pe else "cao hơn"
        r.append(f"P/E {rel.current_pe:.1f} {direction} ngành {rel.sector_median_pe:.1f} ({rel.peer_count} peer VN30)")
    if rel.current_pb:
        r.append(f"P/B: {rel.current_pb:.2f}x")
    if rel.dividend_yield:
        r.append(f"Dividend yield: {rel.dividend_yield*100:.2f}%")
    if quality.f_score is not None:
        denom = quality.f_score_applicable
        if denom < 9:
            # Bank: show passed/applicable so it's clear the denominator is smaller
            passed_applicable = round((quality.f_score_pct or 0) * denom)
            r.append(f"F-score {passed_applicable}/{denom} (áp dụng)")
        else:
            r.append(f"F-score: {quality.f_score}/{denom}")
    if quality.z_score is not None:
        r.append(f"Altman Z': {quality.z_score:.2f} ({quality.z_interpretation})")
    return r


def recommend(
    ticker: str,
    src: StockDataSource,
    company: Optional[CompanyInfo] = None,
    cfg: Optional[dict] = None,
) -> ValuationResult:
    """Full valuation pipeline → ValuationResult. Never raises."""
    if cfg is None:
        cfg = _load_cfg()

    reco_cfg = cfg.get("recommendation", {})
    buy_t = reco_cfg.get("buy_upside_threshold", 0.20)
    sell_t = reco_cfg.get("sell_downside_threshold", -0.10)
    disclaimer = cfg.get("disclaimer", "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư.")

    if company is None:
        company = src.get_company(ticker)
    current_price = company.current_price if company else 0.0

    dcf = run_dcf(ticker, src, company=company, cfg=cfg)
    rel = run_relative(ticker, src, company=company, cfg=cfg)
    quality = run_quality(ticker, src, company=company)

    blend = cfg.get("blend", {})
    target = _blend_target(dcf, rel, blend.get("dcf_weight", 0.5), blend.get("relative_weight", 0.5))
    upside = (target - current_price) / current_price if target and current_price > 0 else None

    up_comp = _upside_score(upside or 0.0, buy_t, sell_t)
    z_comp = _z_component(quality.z_score, quality.z_score_applicable)
    # Use normalized fraction (passed / applicable) so banks are not penalised for
    # structurally missing criteria (F5, F8) that are inapplicable to the sector.
    score = _blend_score(up_comp, _f_component(quality.f_score_pct), z_comp, cfg.get("score", {}))
    reco = _recommendation(upside, buy_t, sell_t)
    reasons = _build_reasons(dcf, rel, quality, target, upside, current_price)

    logger.info(
        f"{ticker}: {reco} score={score} target={target and target/1000:.1f}k "
        f"upside={upside and upside*100:+.1f}% F={quality.f_score} Z={quality.z_score}"
    )
    return ValuationResult(
        ticker=ticker, current_price=current_price,
        intrinsic_value=dcf.intrinsic_value, target_price=target,
        upside_pct=upside, score=score, recommendation=reco,
        f_score=quality.f_score,
        f_score_applicable=quality.f_score_applicable,
        f_score_pct=quality.f_score_pct,
        z_score=quality.z_score,
        dcf_applicable=dcf.dcf_applicable, reasons=reasons,
        disclaimer=disclaimer, sensitivity=dcf.sensitivity,
    )
