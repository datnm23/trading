"""Data fetching helpers for the screener engine.

Isolates all source.get_* calls so engine.py stays under 200 LOC.
All errors are caught and degraded gracefully (empty model returned).
"""

from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios


def fetch_ticker_data(
    source: StockDataSource,
    ticker: str,
    start: str,
    end: str,
    period: str,
) -> tuple[pd.DataFrame, FinancialStatement, Ratios, Optional[CompanyInfo]]:
    """Fetch all four data kinds for one ticker. Never raises."""
    ohlcv = pd.DataFrame()
    income = FinancialStatement(ticker=ticker, statement_type="income_statement", period=period)
    ratios = Ratios(ticker=ticker, period=period)
    company: Optional[CompanyInfo] = None
    try:
        ohlcv = source.get_ohlcv(ticker, start, end)
        income = source.get_financials(ticker, "income_statement", period=period)
        ratios = source.get_ratios(ticker, period=period)
        company = source.get_company(ticker)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[{ticker}] data fetch error: {exc}")
    return ohlcv, income, ratios, company


def fetch_all(
    source: StockDataSource,
    tickers: List[str],
    start: str,
    end: str,
    period: str,
) -> tuple[
    Dict[str, pd.DataFrame],
    Dict[str, FinancialStatement],
    Dict[str, Ratios],
    Dict[str, Optional[CompanyInfo]],
]:
    """Batch-fetch data for all tickers. Returns four dicts keyed by ticker."""
    all_ohlcv: Dict[str, pd.DataFrame] = {}
    all_income: Dict[str, FinancialStatement] = {}
    all_ratios: Dict[str, Ratios] = {}
    all_companies: Dict[str, Optional[CompanyInfo]] = {}

    for ticker in tickers:
        ohlcv, income, ratios, company = fetch_ticker_data(source, ticker, start, end, period)
        all_ohlcv[ticker] = ohlcv
        all_income[ticker] = income
        all_ratios[ticker] = ratios
        all_companies[ticker] = company

    return all_ohlcv, all_income, all_ratios, all_companies


def load_vnindex(source: StockDataSource, start: str, end: str) -> Optional[pd.DataFrame]:
    """Attempt to load VN-Index OHLCV. Returns None on any failure (degrade gracefully)."""
    try:
        df = source.get_ohlcv("VNINDEX", start, end, interval="1D")
        if df is not None and not df.empty:
            return df
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"VN-Index fetch failed: {exc}; RS filter will be N/A")
    return None
