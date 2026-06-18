"""Relative valuation: P/E vs sector & history, P/B, dividend yield.

Implied value = sector_median_pe * EPS (or own historical median P/E * EPS as fallback).
Degrades gracefully when peers or ratios are missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo
from data.vn.universe import get_vn30, is_bank


@dataclass
class RelativeResult:
    ticker: str
    current_pe: Optional[float]
    current_pb: Optional[float]
    sector_median_pe: Optional[float]
    own_historical_median_pe: Optional[float]
    peer_count: int
    eps: Optional[float]                       # VND/share (absolute)
    implied_value_pe: Optional[float]          # VND/share from peer P/E * EPS
    dividend_yield: Optional[float]            # fraction e.g. 0.03
    notes: list[str] = field(default_factory=list)


def _latest_value(items: dict, key: str) -> Optional[float]:
    period_vals = items.get(key, {})
    if not period_vals:
        return None
    for label in sorted(period_vals.keys(), reverse=True):
        v = period_vals[label]
        if v is not None:
            return float(v)
    return None


def _historical_median(items: dict, key: str, n_years: int = 5) -> Optional[float]:
    """Median of last n_years values for a ratio key.

    De-duplicates period labels before slicing to avoid double-counting when the
    same period appears more than once in period_labels (e.g. quarterly snapshots
    that repeat an annual label).
    """
    period_vals = items.get(key, {})
    if not period_vals:
        return None
    # De-dupe: dict.keys() are already unique by definition, but callers may feed
    # derived label lists that repeat; using dict keys directly is safe and unique.
    sorted_labels = sorted(set(period_vals.keys()), reverse=True)[:n_years]
    vals = [float(period_vals[l]) for l in sorted_labels if period_vals[l] is not None]
    if not vals:
        return None
    vals_sorted = sorted(vals)
    mid = len(vals_sorted) // 2
    if len(vals_sorted) % 2 == 1:
        return vals_sorted[mid]
    return (vals_sorted[mid - 1] + vals_sorted[mid]) / 2.0


def _collect_peer_pes(
    ticker: str,
    sector: str,
    src: StockDataSource,
    min_peers: int = 3,
) -> tuple[list[float], int]:
    """Collect P/E ratios from VN30 peers in same sector (fallback: all VN30)."""
    vn30 = get_vn30()
    peers = [t for t in vn30 if t != ticker]

    sector_pes: list[float] = []
    for peer in peers:
        info = src.get_company(peer)
        if info is None:
            continue
        if info.sector != sector:
            continue
        r = src.get_ratios(peer, period="year")
        pe = _latest_value(r.items, "pe_ratio")
        if pe and 0 < pe < 200:  # sanity bounds
            sector_pes.append(pe)

    if len(sector_pes) >= min_peers:
        return sector_pes, len(sector_pes)

    # No whole-VN30 fallback: applying one VN30-wide median P/E across every sector
    # produced absurd targets (e.g. VIC P/E 134 → −90% vs a 13.2 median). When there
    # aren't enough same-sector peers, emit nothing so the recommender skips relative
    # valuation rather than fabricating a target.
    logger.debug(f"{ticker}: <{min_peers} same-sector peers — no relative P/E target")
    return [], len(sector_pes)


def _median(vals: list[float]) -> Optional[float]:
    if not vals:
        return None
    s = sorted(vals)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


def run_relative(
    ticker: str,
    src: StockDataSource,
    company: Optional[CompanyInfo] = None,
    cfg: Optional[dict] = None,
) -> RelativeResult:
    """Compute relative valuation for ticker.

    Never raises — degrades gracefully with notes.
    """
    if cfg is None:
        cfg = {}
    rel_cfg = cfg.get("relative", {})
    min_peers = rel_cfg.get("peer_min_count", 3)

    if company is None:
        company = src.get_company(ticker)

    ratios = src.get_ratios(ticker, period="year")
    notes: list[str] = []

    current_pe = _latest_value(ratios.items, "pe_ratio")
    current_pb = _latest_value(ratios.items, "pb_ratio")
    div_yield = _latest_value(ratios.items, "dividend_yield")

    # EPS from income statement (most reliable)
    inc = src.get_financials(ticker, "income_statement", period="year")
    eps = _latest_value(inc.items, "eps_basic_vnd")

    own_hist_pe = _historical_median(ratios.items, "pe_ratio")

    sector = company.sector if company else ""
    sector_pes, peer_count = _collect_peer_pes(ticker, sector, src, min_peers=min_peers)
    sector_median_pe = _median(sector_pes)

    # Implied value: prefer sector median P/E, fallback own historical
    implied_value_pe: Optional[float] = None
    if eps and eps > 0:
        ref_pe = sector_median_pe or own_hist_pe
        if ref_pe:
            implied_value_pe = ref_pe * eps
            notes.append(
                f"Implied value = P/E tham chiếu {ref_pe:.1f} × EPS {eps/1000:.1f}k = "
                f"{implied_value_pe/1000:.1f}k VND/CP"
            )
    else:
        notes.append("Thiếu EPS, không tính implied value từ P/E")

    if current_pe:
        notes.append(f"P/E hiện tại: {current_pe:.1f}")
    if sector_median_pe:
        notes.append(f"P/E trung vị ngành ({peer_count} peer): {sector_median_pe:.1f}")
    if own_hist_pe:
        notes.append(f"P/E lịch sử median: {own_hist_pe:.1f}")
    if current_pb:
        notes.append(f"P/B: {current_pb:.2f}")
    if div_yield:
        notes.append(f"Dividend yield: {div_yield*100:.2f}%")

    logger.debug(
        f"{ticker}: relative PE={current_pe}, sector_med={sector_median_pe}, "
        f"implied={implied_value_pe}"
    )
    return RelativeResult(
        ticker=ticker,
        current_pe=current_pe,
        current_pb=current_pb,
        sector_median_pe=sector_median_pe,
        own_historical_median_pe=own_hist_pe,
        peer_count=peer_count,
        eps=eps,
        implied_value_pe=implied_value_pe,
        dividend_yield=div_yield,
        notes=notes,
    )
