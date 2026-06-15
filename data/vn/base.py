"""Abstract base / Protocol for VN stock data sources."""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from data.vn.models import FinancialStatement, Ratios, CompanyInfo


class StockDataSource(ABC):
    """Protocol for VN stock data adapters.

    All implementors must provide the four data kinds below.
    Returns empty/None gracefully on missing data — never raises on missing ticker.
    """

    @abstractmethod
    def get_ohlcv(
        self,
        ticker: str,
        start: str,
        end: str,
        interval: str = "1D",
    ) -> pd.DataFrame:
        """Return OHLCV DataFrame with columns [time, open, high, low, close, volume].

        Prices are in THOUSANDS of VND (as returned by vnstock).
        time column is datetime. Returns empty DataFrame on failure.
        """

    @abstractmethod
    def get_financials(
        self,
        ticker: str,
        statement_type: str,
        period: str = "year",
    ) -> FinancialStatement:
        """Return FinancialStatement for ticker.

        statement_type: 'balance_sheet' | 'income_statement' | 'cash_flow'
        period: 'year' | 'quarter'
        Returns empty FinancialStatement on failure.
        """

    @abstractmethod
    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        """Return Ratios for ticker.

        period: 'year' | 'quarter'
        Returns empty Ratios on failure.
        """

    @abstractmethod
    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        """Return CompanyInfo for ticker, or None on failure."""
