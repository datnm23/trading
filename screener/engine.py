"""Screener engine: load config → fetch data → apply filters → rank watchlist.

Usage:
    from screener import ScreenerEngine
    engine = ScreenerEngine(source, config_path="config/screener.yaml")
    watchlist = engine.screen()               # uses VN30 universe
    watchlist = engine.screen(["FPT", "VCB"])
"""

from datetime import date
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional

import yaml
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, Ratios
from data.vn.universe import get_universe

from screener.data_fetcher import fetch_all, load_vnindex
from screener.filters.fundamental import (
    filter_debt_to_equity, filter_eps_growth, filter_net_margin,
    filter_pe_ratio, filter_revenue_growth, filter_roe,
    _latest_ratio,
)
from screener.filters.technical import (
    filter_liquidity, filter_price_above_ma, filter_relative_strength,
)
from screener.scorer import CriterionResult, WatchlistItem, rank_watchlist

import pandas as pd


# ---------------------------------------------------------------------------
# Sector-median P/E helper
# ---------------------------------------------------------------------------

def _sector_median_pe(
    all_ratios: Dict[str, Ratios],
    all_companies: Dict[str, Optional[CompanyInfo]],
    ticker: str,
) -> Optional[float]:
    """Sector-median P/E for ticker. Falls back to universe median when <3 peers."""
    target = all_companies.get(ticker)
    target_sector = target.sector if target else None

    def _pe(t: str) -> Optional[float]:
        v = _latest_ratio(all_ratios.get(t, Ratios(ticker=t, period="year")), "pe_ratio")
        return v if (v is not None and v > 0) else None

    if target_sector:
        peers = [t for t, c in all_companies.items()
                 if c and c.sector == target_sector and t != ticker]
        peer_pes = [p for t in peers if (p := _pe(t)) is not None]
        if len(peer_pes) >= 3:
            return median(peer_pes)
        logger.debug(f"[{ticker}] <3 sector P/E peers; using universe median")

    # Exclude the target ticker from the universe-median so a stock never
    # benchmarks its own P/E against itself (critical in small universes).
    all_pes = [p for t in all_ratios if t != ticker and (p := _pe(t)) is not None]
    return median(all_pes) if all_pes else None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ScreenerEngine:
    """Config-driven FA+TA screener over a universe of VN tickers."""

    def __init__(self, source: StockDataSource, config_path: str = "config/screener.yaml"):
        self.source = source
        cfg_file = Path(config_path)
        if not cfg_file.exists():
            raise FileNotFoundError(f"Screener config not found: {config_path}")
        with cfg_file.open() as f:
            self.cfg = yaml.safe_load(f)

    def screen(self, universe: Optional[List[str]] = None) -> List[WatchlistItem]:
        """Run screener → ranked WatchlistItem list."""
        tickers = universe or get_universe("VN30")
        logger.info(f"Screening {len(tickers)} tickers")

        ohlcv_cfg = self.cfg.get("ohlcv", {})
        start = ohlcv_cfg.get("start_date", "2023-01-01")
        end = ohlcv_cfg.get("end_date") or date.today().isoformat()
        period = self.cfg.get("data_period", "year")

        all_ohlcv, all_income, all_ratios, all_companies = fetch_all(
            self.source, tickers, start, end, period
        )
        vnindex = load_vnindex(self.source, start, end)

        per_ticker: Dict[str, List[CriterionResult]] = {}
        for ticker in tickers:
            try:
                per_ticker[ticker] = self._apply_filters(
                    ticker=ticker,
                    ohlcv=all_ohlcv[ticker],
                    income=all_income[ticker],
                    ratios=all_ratios[ticker],
                    company=all_companies[ticker],
                    vnindex_ohlcv=vnindex,
                    all_ratios=all_ratios,
                    all_companies=all_companies,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(f"[{ticker}] filter error: {exc}; skipping")

        watchlist = rank_watchlist(per_ticker)
        logger.info(f"Done. Top: {watchlist[0].ticker if watchlist else 'none'}")
        return watchlist

    # ------------------------------------------------------------------
    # Internal: apply all enabled filters for one ticker
    # ------------------------------------------------------------------

    def _apply_filters(
        self,
        ticker: str,
        ohlcv: pd.DataFrame,
        income,
        ratios: Ratios,
        company: Optional[CompanyInfo],
        vnindex_ohlcv: Optional[pd.DataFrame],
        all_ratios: Dict[str, Ratios],
        all_companies: Dict[str, Optional[CompanyInfo]],
    ) -> List[CriterionResult]:
        is_bank = company.is_bank if company else False
        fa = self.cfg.get("fundamentals", {})
        ta = self.cfg.get("technicals", {})
        out: List[CriterionResult] = []

        def _add(key: str, cfg_section: dict, fn_result):
            passed, value, label = fn_result
            out.append(CriterionResult(key, label, passed, value,
                                       cfg_section.get("weight", 1.0)))

        # FA
        if fa.get("roe", {}).get("enabled", True):
            c = fa["roe"]
            _add("roe", c, filter_roe(ratios, c.get("threshold", 0.15)))

        if fa.get("pe_ratio", {}).get("enabled", True):
            c = fa["pe_ratio"]
            sec_med = _sector_median_pe(all_ratios, all_companies, ticker)
            _add("pe_ratio", c, filter_pe_ratio(ratios, c.get("threshold", 25.0), sec_med))

        if fa.get("eps_growth", {}).get("enabled", True):
            c = fa["eps_growth"]
            _add("eps_growth", c, filter_eps_growth(income, c.get("threshold", 0.0)))

        if fa.get("revenue_growth", {}).get("enabled", True):
            c = fa["revenue_growth"]
            _add("revenue_growth", c,
                 filter_revenue_growth(income, is_bank=is_bank, threshold=c.get("threshold", 0.0)))

        if fa.get("debt_to_equity", {}).get("enabled", True):
            c = fa["debt_to_equity"]
            _add("debt_to_equity", c,
                 filter_debt_to_equity(ratios, is_bank=is_bank, threshold=c.get("threshold", 1.0)))

        if fa.get("net_margin", {}).get("enabled", True):
            c = fa["net_margin"]
            _add("net_margin", c, filter_net_margin(ratios, c.get("threshold", 0.05)))

        # TA
        if ta.get("price_above_ma", {}).get("enabled", True):
            c = ta["price_above_ma"]
            _add("price_above_ma", c,
                 filter_price_above_ma(ohlcv, c.get("ma50_period", 50), c.get("ma200_period", 200)))

        if ta.get("relative_strength", {}).get("enabled", True):
            c = ta["relative_strength"]
            _add("relative_strength", c,
                 filter_relative_strength(ohlcv, vnindex_ohlcv, c.get("lookback_days", 60)))

        if ta.get("liquidity", {}).get("enabled", True):
            c = ta["liquidity"]
            _add("liquidity", c,
                 filter_liquidity(ohlcv, c.get("threshold", 10_000_000_000),
                                  c.get("lookback_days", 20)))

        return out
