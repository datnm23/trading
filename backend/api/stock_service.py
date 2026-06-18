"""StockService — wraps screener + valuation + data layer for advisory endpoints.

Accepts an injected StockDataSource for testability (no live fetch at import).
"""

from typing import List, Optional
from pathlib import Path

from loguru import logger

from datetime import date, timedelta

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, Ratios
from data.vn.universe import get_vn30, get_company_meta
from screener import ScreenerEngine, WatchlistItem
from screener.filters.fundamental import _latest_ratio
from valuation import recommend, ValuationResult
from data.vn.financials_store import FinancialsStore
from journal.recommendation_logger import RecommendationLogger
from backend.api.models import (
    CriterionDetail,
    CompanySummary,
    FinancialLineItem,
    FinancialsResponse,
    FinancialStatementView,
    FinancialSummary,
    MarketIndexView,
    MarketOverviewResponse,
    MarketStock,
    PriceSummary,
    RecommendationRead,
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
        self._fin_store: Optional[FinancialsStore] = None
        self._journal: Optional[RecommendationLogger] = None

    def _get_fin_store(self) -> FinancialsStore:
        if self._fin_store is None:
            self._fin_store = FinancialsStore()  # PG if reachable, else SQLite
        return self._fin_store

    def _get_journal(self) -> RecommendationLogger:
        if self._journal is None:
            self._journal = RecommendationLogger()  # PG if TRADING_DB_URL, else SQLite
        return self._journal

    def get_financials(self, ticker: str, period_type: str = "year") -> FinancialsResponse:
        """Read stored BS/IS/CF for a ticker from FinancialsStore (collected via
        scripts/collect_vn30_financials.py). Returns empty statements if none."""
        data = self._get_fin_store().get_ticker_financials(ticker.upper(), period_type)
        statements: List[FinancialStatementView] = []
        # stable display order
        for stmt in ("balance_sheet", "income_statement", "cash_flow"):
            s = data.get(stmt)
            if not s:
                continue
            rows = [
                FinancialLineItem(item_id=iid, label=s["labels"].get(iid, iid), values=vals)
                for iid, vals in s["values"].items()
            ]
            statements.append(FinancialStatementView(
                statement_type=stmt, periods=s["periods"], rows=rows))
        return FinancialsResponse(ticker=ticker.upper(), period_type=period_type, statements=statements)

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
            self._log_recommendation(result)
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

    def _log_recommendation(self, result: ValuationResult) -> None:
        """Persist a valuation to the recommendation journal, once per ticker/day.

        Best-effort: a journal failure must never break the valuation response.
        """
        try:
            jnl = self._get_journal()
            today = date.today().isoformat()
            recent = jnl.get_recommendations(ticker=result.ticker, limit=1)
            if recent and str(recent[0].get("date")) == today:
                return  # already logged today
            jnl.log_recommendation(
                result.ticker, today, result.recommendation,
                target_price=result.target_price,
                current_price=result.current_price,
                score=result.score,
                upside_pct=result.upside_pct,
                reasons=result.reasons,
            )
        except Exception as exc:  # noqa: BLE001 — journaling is non-critical
            logger.warning(f"[{result.ticker}] journal log skipped: {exc}")

    def get_recommendations(self, ticker: Optional[str] = None, limit: int = 100) -> List[RecommendationRead]:
        """Read the recommendation journal, newest first."""
        try:
            rows = self._get_journal().get_recommendations(ticker=ticker, limit=limit)
            return [
                RecommendationRead(
                    id=int(r["id"]),
                    ticker=r["ticker"],
                    date=str(r["date"]),
                    recommendation=r["recommendation"],
                    target_price=r.get("target_price"),
                    current_price=r.get("current_price"),
                    score=r.get("score"),
                    upside_pct=r.get("upside_pct"),
                    reasons=r.get("reasons", []),
                    created_at=str(r.get("created_at", "")),
                )
                for r in rows
            ]
        except Exception as exc:
            logger.error(f"get_recommendations failed: {exc}")
            return []

    def get_market_overview(self) -> MarketOverviewResponse:
        """VN-Index summary + VN30 price/%change table (DNSE closes, cached)."""
        end = date.today()
        start = end - timedelta(days=40)
        s, e = start.isoformat(), end.isoformat()

        # VN-Index (index points — not VND)
        index_view: Optional[MarketIndexView] = None
        try:
            idx = self.source.get_ohlcv("VNINDEX", s, e, "1D")
            if idx is not None and not idx.empty:
                closes = [float(c) for c in idx["close"].tolist()]
                last = closes[-1]
                prev = closes[-2] if len(closes) >= 2 else last
                index_view = MarketIndexView(
                    symbol="VNINDEX", value=last,
                    change_pct=((last - prev) / prev * 100) if prev else None,
                    series=closes[-30:],
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"VN-Index overview failed: {exc}")

        stocks: List[MarketStock] = []
        for t in get_vn30():
            try:
                df = self.source.get_ohlcv(t, s, e, "1D")
                if df is None or df.empty:
                    continue
                closes = df["close"].tolist()
                last = float(closes[-1])
                prev = float(closes[-2]) if len(closes) >= 2 else last
                name, sector = get_company_meta(t)
                stocks.append(MarketStock(
                    ticker=t, name=name, sector=sector,
                    price=last * 1000.0,  # thousands VND → absolute VND
                    change_pct=((last - prev) / prev * 100) if prev else None,
                ))
            except Exception as exc:  # noqa: BLE001 — skip a bad ticker, keep the rest
                logger.warning(f"[{t}] market row failed: {exc}")
        return MarketOverviewResponse(index=index_view, stocks=stocks)

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
