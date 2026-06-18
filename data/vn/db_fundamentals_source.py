"""DB-backed fundamentals source — serves financials/ratios/company WITHOUT live vnstock.

Why: live vnstock calls at request time rate-limit (20 req/min guest) and can
hard-terminate the process, causing 61s stock-detail loads and 500s on valuation
(relative valuation fans out P/E across ~29 VN30 peers). All fundamentals we need
are already collected into the DB (vn_financials, via collect_vn30_financials.py),
and prices come from DNSE chart-api (no rate-limit, adjusted).

This source composes:
  - OHLCV / price          -> delegated to a price_source (CachedDataSource(DnseSource))
  - financials (BS/IS/CF)  -> FinancialsStore (DB)
  - ratios (computed)      -> derived from DB financials + latest DNSE price
  - company                -> static VN30 metadata + DNSE price + derived shares

Ratios computed (annual, latest period):
  eps_basic_vnd, pe_ratio, pb_ratio, roe, net_margin, debt_to_equity
Missing inputs degrade to None (never raises) — banks lack net_sales, etc.

Units: DNSE close is in THOUSANDS of VND; CompanyInfo.current_price /
market_cap are ABSOLUTE VND (per data.vn.models contract), so price is ×1000.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.financials_store import FinancialsStore
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from data.vn.universe import get_company_meta, is_bank

_PRICE_LOOKBACK_DAYS = 15  # enough trading days to find a recent close


def _latest(items: dict, key: str) -> Optional[float]:
    """Latest numeric value for an item_id across period labels (max label = newest)."""
    per = items.get(key)
    if not per:
        return None
    numeric = {k: v for k, v in per.items() if isinstance(v, (int, float))}
    if not numeric:
        return None
    return numeric[max(numeric.keys())]


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


class DbFundamentalsSource(StockDataSource):
    """Unified advisory source: DNSE prices + DB fundamentals (no live vnstock)."""

    def __init__(self, price_source: StockDataSource, fin_store: Optional[FinancialsStore] = None):
        """
        Args:
            price_source: source used for OHLCV (e.g. CachedDataSource(DnseSource())).
            fin_store: FinancialsStore for DB financials (built if None).
        """
        self.price_source = price_source
        self.store = fin_store or FinancialsStore()

    # ------------------------------------------------------------------
    # OHLCV — delegated to price source
    # ------------------------------------------------------------------
    def get_ohlcv(self, ticker: str, start: str, end: str, interval: str = "1D") -> pd.DataFrame:
        return self.price_source.get_ohlcv(ticker, start, end, interval)

    def _latest_price_vnd(self, ticker: str) -> float:
        """Most recent close in ABSOLUTE VND (DNSE close ×1000). 0.0 if unavailable."""
        end = datetime.utcnow().date()
        start = end - timedelta(days=_PRICE_LOOKBACK_DAYS)
        try:
            df = self.get_ohlcv(ticker, start.isoformat(), end.isoformat(), "1D")
            if df is None or df.empty or "close" not in df.columns:
                return 0.0
            return float(df["close"].iloc[-1]) * 1000.0
        except Exception as exc:  # noqa: BLE001 — degrade gracefully
            logger.warning(f"[{ticker}] price fetch failed: {exc}")
            return 0.0

    # ------------------------------------------------------------------
    # Financials — from DB
    # ------------------------------------------------------------------
    def get_financials(
        self, ticker: str, statement_type: str, period: str = "year"
    ) -> FinancialStatement:
        data = self.store.get_ticker_financials(ticker.upper(), period)
        s = data.get(statement_type)
        if not s:
            return FinancialStatement(ticker=ticker.upper(), statement_type=statement_type, period=period)
        return FinancialStatement(
            ticker=ticker.upper(),
            statement_type=statement_type,
            period=period,
            items=s["values"],
            labels=s["labels"],
        )

    # ------------------------------------------------------------------
    # Derived shares (from EPS) — shared by ratios + company
    # ------------------------------------------------------------------
    def _shares_outstanding(self, ticker: str, inc_items: dict) -> Optional[float]:
        """Shares outstanding — authoritative DB value first, else estimate.

        Preferred: real issue_share collected offline into vn_shares (collector).
        Fallback: net profit attributable to parent / basic EPS — unreliable
        (EPS share base ≠ profit base; off ~2× for some tickers), kept only so
        tickers not yet collected degrade gracefully instead of returning None.
        """
        real = self.store.get_shares(ticker)
        if real and real > 0:
            return real
        eps = _latest(inc_items, "eps_basic_vnd")
        profit = _latest(inc_items, "attributable_to_parent_company") \
            or _latest(inc_items, "net_profit_loss_after_tax")
        if eps and eps > 0 and profit:
            return profit / eps
        return None

    # ------------------------------------------------------------------
    # Ratios — computed from DB financials + DNSE price
    # ------------------------------------------------------------------
    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        ticker = ticker.upper()
        data = self.store.get_ticker_financials(ticker, period)
        inc = (data.get("income_statement") or {}).get("values", {})
        bs = (data.get("balance_sheet") or {}).get("values", {})
        if not inc and not bs:
            return Ratios(ticker=ticker, period=period)

        eps = _latest(inc, "eps_basic_vnd")
        net_profit = _latest(inc, "net_profit_loss_after_tax")
        net_sales = _latest(inc, "net_sales")
        equity = _latest(bs, "owners_equity")
        liabilities = _latest(bs, "liabilities")
        shares = self._shares_outstanding(ticker, inc)
        price = self._latest_price_vnd(ticker)

        computed: dict = {
            "eps_basic_vnd": eps,
            "pe_ratio": _safe_div(price, eps) if price else None,
            "pb_ratio": _safe_div(price, _safe_div(equity, shares)) if price else None,
            "roe": _safe_div(net_profit, equity),
            "net_margin": _safe_div(net_profit, net_sales),
            "debt_to_equity": _safe_div(liabilities, equity),
        }
        # ref label = newest period present in income statement
        label = None
        if inc.get("eps_basic_vnd"):
            label = max(inc["eps_basic_vnd"].keys())
        label = label or "latest"
        items = {k: {label: v} for k, v in computed.items() if v is not None}
        return Ratios(ticker=ticker, period=period, items=items, period_labels=[label])

    # ------------------------------------------------------------------
    # Company — static metadata + DNSE price + derived shares
    # ------------------------------------------------------------------
    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        ticker = ticker.upper()
        name, sector = get_company_meta(ticker)
        price = self._latest_price_vnd(ticker)
        data = self.store.get_ticker_financials(ticker, "year")
        inc = (data.get("income_statement") or {}).get("values", {})
        shares = self._shares_outstanding(ticker, inc) or 0.0
        return CompanyInfo(
            ticker=ticker,
            organ_name=name,
            organ_short_name=name,
            sector=sector,
            market_cap=price * shares,
            current_price=price,
            issue_share=shares,
            is_bank=is_bank(ticker),
        )
