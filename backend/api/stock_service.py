"""StockService — wraps screener + valuation + data layer for advisory endpoints.

Accepts an injected StockDataSource for testability (no live fetch at import).
"""

from typing import List, Optional
from pathlib import Path

from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, Ratios
from screener import ScreenerEngine, WatchlistItem
from screener.filters.fundamental import _latest_ratio
from valuation import recommend, ValuationResult
from backend.api.models import (
    CriterionDetail,
    CompanySummary,
    FinancialSummary,
    PriceSummary,
    ScreenerItem,
    StockDetail,
    ValuationResponse,
)

_SCREENER_CONFIG = str(Path(__file__).parent.parent.parent / "config" / "screener.yaml")


class StockService:
    """Advisory service layer. source is injected — never fetched at import time."""

    def __init__(self, source: StockDataSource) -> None:
        self.source = source
        self._screener: Optional[ScreenerEngine] = None

    def _get_screener(self) -> ScreenerEngine:
        if self._screener is None:
            self._screener = ScreenerEngine(self.source, config_path=_SCREENER_CONFIG)
        return self._screener

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_screener(self, universe: Optional[List[str]] = None) -> List[ScreenerItem]:
        """Run screener and return ranked list."""
        try:
            engine = self._get_screener()
            items: List[WatchlistItem] = engine.screen(universe)
            return [self._watchlist_to_item(w) for w in items]
        except Exception as exc:
            logger.error(f"Screener failed: {exc}")
            return []

    def get_stock_detail(self, ticker: str) -> Optional[StockDetail]:
        """Return price + company + financial summary for ticker."""
        try:
            company = self.source.get_company(ticker)
            if company is None:
                company = CompanyInfo(ticker=ticker)

            ratios = self.source.get_ratios(ticker, period="year")
            fin_summary = self._ratios_to_summary(ratios)

            return StockDetail(
                ticker=ticker,
                company=CompanySummary(
                    name=company.organ_name or ticker,
                    short_name=company.organ_short_name or ticker,
                    sector=company.sector or "",
                    is_bank=company.is_bank,
                    listing_date=company.listing_date or "",
                ),
                price=PriceSummary(
                    current_price=company.current_price,
                    market_cap=company.market_cap,
                    issue_share=company.issue_share,
                    free_float_pct=company.free_float_pct,
                    foreigner_pct=company.foreigner_pct,
                ),
                financials=fin_summary,
            )
        except Exception as exc:
            logger.error(f"[{ticker}] get_stock_detail failed: {exc}")
            return None

    def get_valuation(self, ticker: str) -> Optional[ValuationResponse]:
        """Run full valuation pipeline → ValuationResponse."""
        try:
            result: ValuationResult = recommend(ticker=ticker, src=self.source)
            return ValuationResponse(
                ticker=result.ticker,
                current_price=result.current_price,
                target_price=result.target_price,
                intrinsic_value=result.intrinsic_value,
                upside_pct=result.upside_pct,
                score=result.score,
                recommendation=result.recommendation,
                f_score=result.f_score,
                f_score_applicable=result.f_score_applicable,
                z_score=result.z_score,
                dcf_applicable=result.dcf_applicable,
                reasons=result.reasons,
                disclaimer=result.disclaimer,
            )
        except Exception as exc:
            logger.error(f"[{ticker}] get_valuation failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _watchlist_to_item(w: WatchlistItem) -> ScreenerItem:
        criteria = [
            CriterionDetail(
                key=c.key,
                label=c.label,
                passed=c.passed,
                value=c.value,
                weight=c.weight,
            )
            for c in w.criteria
        ]
        return ScreenerItem(
            ticker=w.ticker,
            score=w.score,
            rank=w.rank,
            passed_count=w.passed_count,
            criteria=criteria,
        )

    @staticmethod
    def _ratios_to_summary(ratios: Ratios) -> FinancialSummary:
        def _get(key: str) -> Optional[float]:
            return _latest_ratio(ratios, key)

        return FinancialSummary(
            pe_ratio=_get("pe_ratio"),
            pb_ratio=_get("pb_ratio"),
            roe=_get("roe"),
            net_margin=_get("net_margin"),
            debt_to_equity=_get("debt_to_equity"),
            eps=_get("eps_basic_vnd"),
        )
