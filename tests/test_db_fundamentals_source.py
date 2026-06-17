"""Offline tests for DbFundamentalsSource — ratio math, units, graceful degradation.

Uses a SQLite-backed FinancialsStore (tmp) + a fake price source (no network).
"""
import pandas as pd
import pytest

from data.vn.base import StockDataSource
from data.vn.db_fundamentals_source import DbFundamentalsSource
from data.vn.financials_store import FinancialsStore
from data.vn.models import FinancialStatement


class _FakePrices(StockDataSource):
    """Returns a single fixed close (in THOUSANDS VND, like DNSE)."""

    def __init__(self, close_thousands: float):
        self.close = close_thousands

    def get_ohlcv(self, ticker, start, end, interval="1D"):
        return pd.DataFrame({"time": [pd.Timestamp("2026-06-16")], "close": [self.close]})

    def get_financials(self, ticker, statement_type, period="year"):
        return FinancialStatement(ticker=ticker, statement_type=statement_type, period=period)

    def get_ratios(self, ticker, period="year"):
        raise NotImplementedError

    def get_company(self, ticker):
        return None


def _seed_store(tmp_path) -> FinancialsStore:
    store = FinancialsStore(db_url=None, sqlite_path=str(tmp_path / "fin.db"))
    # Income statement: EPS 5000 VND, profit 10e12, net_sales 100e12 → margin 10%
    store.store_statement(FinancialStatement(
        ticker="FPT", statement_type="income_statement", period="year",
        items={
            "eps_basic_vnd": {"2025": 5000.0, "2024": 4000.0},
            "net_profit_loss_after_tax": {"2025": 10e12, "2024": 8e12},
            "attributable_to_parent_company": {"2025": 10e12, "2024": 8e12},
            "net_sales": {"2025": 100e12, "2024": 80e12},
        }, labels={}), max_periods=2, source="test")
    # Balance sheet: equity 50e12, liabilities 25e12 → D/E 0.5, ROE 20%
    store.store_statement(FinancialStatement(
        ticker="FPT", statement_type="balance_sheet", period="year",
        items={
            "owners_equity": {"2025": 50e12, "2024": 40e12},
            "liabilities": {"2025": 25e12, "2024": 20e12},
        }, labels={}), max_periods=2, source="test")
    return store


def test_ratios_computed_from_db_and_price(tmp_path):
    store = _seed_store(tmp_path)
    # close = 75 (thousands) → 75,000 VND absolute
    src = DbFundamentalsSource(price_source=_FakePrices(75.0), fin_store=store)
    r = src.get_ratios("FPT")
    items = r.items
    label = r.period_labels[0]
    assert items["eps_basic_vnd"][label] == 5000.0
    # P/E = 75000 / 5000 = 15
    assert items["pe_ratio"][label] == pytest.approx(15.0)
    # ROE = 10e12 / 50e12 = 0.2
    assert items["roe"][label] == pytest.approx(0.2)
    # net_margin = 10e12 / 100e12 = 0.1
    assert items["net_margin"][label] == pytest.approx(0.1)
    # D/E = 25e12 / 50e12 = 0.5
    assert items["debt_to_equity"][label] == pytest.approx(0.5)
    # shares = 10e12 / 5000 = 2e9 ; BVPS = 50e12/2e9 = 25000 ; P/B = 75000/25000 = 3
    assert items["pb_ratio"][label] == pytest.approx(3.0)


def test_company_price_shares_marketcap(tmp_path):
    store = _seed_store(tmp_path)
    src = DbFundamentalsSource(price_source=_FakePrices(75.0), fin_store=store)
    c = src.get_company("FPT")
    assert c.current_price == pytest.approx(75_000.0)        # absolute VND
    assert c.issue_share == pytest.approx(2e9)               # 10e12 / 5000
    assert c.market_cap == pytest.approx(75_000.0 * 2e9)
    assert c.organ_short_name == "Tập đoàn FPT"
    assert c.sector == "Công nghệ"
    assert c.is_bank is False


def test_missing_data_degrades_to_none(tmp_path):
    """No financials in DB → ratios empty, company still returns metadata + price."""
    store = FinancialsStore(db_url=None, sqlite_path=str(tmp_path / "empty.db"))
    src = DbFundamentalsSource(price_source=_FakePrices(50.0), fin_store=store)
    r = src.get_ratios("FPT")
    assert r.items == {}
    c = src.get_company("FPT")
    assert c.current_price == pytest.approx(50_000.0)
    assert c.issue_share == 0.0
    assert c.market_cap == 0.0
