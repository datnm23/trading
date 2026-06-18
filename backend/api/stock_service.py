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
    SignalItem,
    SignalsResponse,
    StockDetail,
    ValuationResponse,
    WikiResult,
    WikiSearchResponse,
)

import time as _time
import threading

# Unified-signal thresholds (tunable). Technical = screener score (0-100, min-max
# normalized across VN30); Value = valuation upside fraction.
_SIGNAL_CFG = {
    "tech_good": 60.0,      # tech score ≥ → TỐT
    "tech_bad": 35.0,       # tech score ≤ → XẤU
    "buy_upside": 0.10,     # upside ≥ +10% → RẺ
    "sell_upside": -0.10,   # upside ≤ −10% → ĐẮT
    "tech_weight": 0.5,     # display-score blend when valuation reliable
    "signals_ttl": 3600,    # cache full VN30 signals 1h (batch build is heavy)
}

# Technical-only screener (point-in-time, validated in backtest). The FA variant
# (config/screener.yaml) uses ~4 recent BCTC periods → look-ahead bias, invalid.
_SCREENER_CONFIG = str(Path(__file__).parent.parent.parent / "config" / "screener-technical.yaml")


class StockService:
    """Advisory service layer. source is injected — never fetched at import time."""

    def __init__(self, source: StockDataSource) -> None:
        self.source = source
        self._screener: Optional[ScreenerEngine] = None
        self._fin_store: Optional[FinancialsStore] = None
        self._journal: Optional[RecommendationLogger] = None
        self._wiki = None  # WikiRAG, lazy (index load is heavy)
        self._signals_cache: Optional[tuple] = None  # (built_at, List[SignalItem])
        self._signals_lock = threading.Lock()  # serialize batch build (no stampede)

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
                reliable=result.reliable,
                reasons=result.reasons,
                disclaimer=result.disclaimer,
            )
        except Exception as exc:
            logger.error(f"[{ticker}] get_valuation failed: {exc}")
            return None

    def _log_signal(self, item: SignalItem) -> None:
        """Persist the UNIFIED signal to the journal, once per ticker/day.

        Logs the matrix action (BUY/SELL/HOLD/INSUFFICIENT) — the single source of
        truth — not the raw valuation reco. Best-effort: never breaks the response.
        """
        try:
            jnl = self._get_journal()
            today = date.today().isoformat()
            recent = jnl.get_recommendations(ticker=item.ticker, limit=1)
            if recent and str(recent[0].get("date")) == today:
                return  # already logged today
            jnl.log_recommendation(
                item.ticker, today, item.action,
                target_price=item.target_price,
                current_price=item.current_price,
                score=int(round(item.score)),
                upside_pct=item.val_upside,
                reasons=item.reasons,
            )
        except Exception as exc:  # noqa: BLE001 — journaling is non-critical
            logger.warning(f"[{item.ticker}] journal log skipped: {exc}")

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

    def search_wiki(self, query: str) -> WikiSearchResponse:
        """Semantic search over the Vietnamese trading knowledge base (WikiRAG)."""
        query = (query or "").strip()
        if not query:
            return WikiSearchResponse(query=query, results=[], count=0)
        try:
            if self._wiki is None:
                from knowledge_engine.rag import WikiRAG
                self._wiki = WikiRAG()  # loads persisted index lazily
            hits = self._wiki.search(query)
            results = [
                WikiResult(
                    id=str(h["document"].get("id", "")),
                    title=h["document"].get("title", ""),
                    content=h["document"].get("content", ""),
                    score=float(h.get("score", 0.0)),
                    source_url=h["document"].get("source_url", ""),
                )
                for h in hits
            ]
            return WikiSearchResponse(query=query, results=results, count=len(results))
        except Exception as exc:
            logger.error(f"wiki search failed for {query!r}: {exc}")
            return WikiSearchResponse(query=query, results=[], count=0)

    # ------------------------------------------------------------------
    # Unified signal — technical (screener) × value (valuation) decision matrix
    # ------------------------------------------------------------------
    def _decide(self, tech_score: Optional[float], upside: Optional[float], reliable: bool) -> str:
        """2-axis decision matrix → BUY | SELL | HOLD | INSUFFICIENT."""
        cfg = _SIGNAL_CFG
        tech_good = tech_score is not None and tech_score >= cfg["tech_good"]
        tech_bad = tech_score is not None and tech_score <= cfg["tech_bad"]
        if not reliable or upside is None:
            # No trustworthy value: never fabricate BUY/SELL.
            return "HOLD" if tech_good else "INSUFFICIENT"
        val_cheap = upside >= cfg["buy_upside"]
        val_rich = upside <= cfg["sell_upside"]
        if tech_good and val_cheap:
            return "BUY"
        if tech_bad and val_rich:
            return "SELL"
        return "HOLD"

    def _display_score(self, tech_score: Optional[float], upside: Optional[float], reliable: bool) -> float:
        """0-100 ranking score: blend tech + value when reliable, else tech only."""
        tech = tech_score if tech_score is not None else 0.0
        if not reliable or upside is None:
            return round(tech, 1)
        # Map upside [-0.30, +0.30] → [0, 100], clamped.
        val_norm = max(0.0, min(100.0, (upside + 0.30) / 0.60 * 100.0))
        w = _SIGNAL_CFG["tech_weight"]
        return round(w * tech + (1 - w) * val_norm, 1)

    def _build_signals(self) -> List[SignalItem]:
        """Build unified signals for the whole VN30 (one screener run + per-ticker valuation)."""
        tech_scores: dict = {}
        try:
            for w in self._get_screener().screen(get_vn30()):
                tech_scores[w.ticker] = w.score
        except Exception as exc:
            logger.error(f"signal: screener run failed: {exc}")

        items: List[SignalItem] = []
        for t in get_vn30():
            name, sector = get_company_meta(t)
            tech = tech_scores.get(t)
            val = self.get_valuation(t)  # cached OHLCV/financials; logs journal once/day
            upside = val.upside_pct if val else None
            reliable = bool(val.reliable) if val else False
            action = self._decide(tech, upside, reliable)
            items.append(SignalItem(
                ticker=t, name=name, sector=sector,
                action=action,
                score=self._display_score(tech, upside, reliable),
                tech_score=round(tech, 1) if tech is not None else None,
                val_upside=upside, reliable=reliable,
                current_price=val.current_price if val else None,
                target_price=val.target_price if val else None,
                reasons=(val.reasons[:3] if val else []),
            ))
            self._log_signal(items[-1])
        items.sort(key=lambda x: x.score, reverse=True)
        return items

    def get_signals(self) -> List[SignalItem]:
        """Cached unified signals for VN30 (TTL). Single source of truth for all pages.

        Build is serialized by a lock (no cache stampede); routes calling this run in
        the threadpool (plain `def` handlers) so the event loop never blocks on the
        ~30-ticker build. Returns a copy so callers can't mutate the shared cache.
        """
        ttl = _SIGNAL_CFG["signals_ttl"]
        cache = self._signals_cache
        if cache and (_time.time() - cache[0]) < ttl:
            return list(cache[1])
        with self._signals_lock:
            cache = self._signals_cache  # re-check: another thread may have built it
            if cache and (_time.time() - cache[0]) < ttl:
                return list(cache[1])
            items = self._build_signals()
            # Don't cache a degraded build (screener produced no tech scores) — a
            # transient data hiccup shouldn't poison the cache for the full TTL.
            if any(it.tech_score is not None for it in items):
                self._signals_cache = (_time.time(), items)
            else:
                self._signals_cache = None
            return list(items)

    def get_signal(self, ticker: str) -> Optional[SignalItem]:
        """Single ticker signal — read from the cached VN30 batch (keeps pages consistent)."""
        ticker = ticker.upper()
        for it in self.get_signals():
            if it.ticker == ticker:
                return it
        return None

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
