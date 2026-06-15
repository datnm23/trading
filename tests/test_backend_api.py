"""Offline tests for VN Stock Advisory backend API.

No live vnstock calls. No DB required.
All data served by FakeSource + FakeStockService.

Run: python3 -m pytest tests/test_backend_api.py -q
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import List, Optional

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from backend.api.main import create_app
from backend.api.models import DISCLAIMER
from backend.api.stock_service import StockService
from journal.recommendation_logger import RecommendationLogger

# ---------------------------------------------------------------------------
# FakeSource — deterministic offline fixture
# ---------------------------------------------------------------------------

def _ohlcv(n: int = 250, close: float = 73.5) -> pd.DataFrame:
    dates = pd.date_range("2023-01-02", periods=n, freq="B")
    return pd.DataFrame({
        "time": dates, "open": close * 0.99, "high": close * 1.01,
        "low": close * 0.98, "close": close, "volume": 5_000_000,
    })


class FakeSource(StockDataSource):
    """Minimal deterministic fake for FPT."""

    def get_ohlcv(self, ticker, start, end, interval="1D") -> pd.DataFrame:
        return _ohlcv()

    def get_financials(self, ticker, statement_type, period="year") -> FinancialStatement:
        items: dict = {}
        if statement_type == "income_statement":
            items = {
                "eps_basic_vnd": {"2024": 5_000.0, "2023": 4_000.0},
                "net_sales":     {"2024": 60e12,   "2023": 50e12},
                "net_profit":    {"2024": 7.2e12,  "2023": 6e12},
            }
        elif statement_type == "balance_sheet":
            items = {
                "total_assets":       {"2024": 50e12},
                "total_liabilities":  {"2024": 20e12},
                "equity":             {"2024": 30e12},
                "current_assets":     {"2024": 25e12},
                "current_liabilities":{"2024": 12e12},
                "long_term_debt":     {"2024": 5e12},
                "retained_earnings":  {"2024": 15e12},
                "ebit":               {"2024": 8e12},
                "interest_expense":   {"2024": 0.5e12},
                "operating_revenue":  {"2024": 60e12},
            }
        elif statement_type == "cash_flow":
            items = {
                "operating_cash_flow": {"2024": 8e12, "2023": 6e12},
                "net_income":          {"2024": 7.2e12, "2023": 6e12},
                "capex":               {"2024": -2e12},
            }
        return FinancialStatement(ticker=ticker, statement_type=statement_type,
                                  period=period, items=items)

    def get_ratios(self, ticker, period="year") -> Ratios:
        return Ratios(
            ticker=ticker, period=period,
            items={
                "roe":            {"2024q4": 0.25},
                "pe_ratio":       {"2024q4": 18.0},
                "pb_ratio":       {"2024q4": 3.5},
                "debt_to_equity": {"2024q4": 0.4},
                "net_margin":     {"2024q4": 0.12},
                "eps_basic_vnd":  {"2024q4": 5_000.0},
            },
            period_labels=["2024q4"],
        )

    def get_company(self, ticker) -> Optional[CompanyInfo]:
        return CompanyInfo(
            ticker=ticker,
            organ_name="FPT Corporation",
            organ_short_name="FPT",
            sector="Technology",
            current_price=73_500.0,
            market_cap=200e12,
            issue_share=1e9,
            is_bank=False,
            listing_date="2006-12-13",
        )


# ---------------------------------------------------------------------------
# App fixture with injected FakeSource
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    fake_svc = StockService(FakeSource())
    app = create_app(stock_service=fake_svc)
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "advisory" in data.get("service", "")


# ---------------------------------------------------------------------------
# Screener
# ---------------------------------------------------------------------------

def test_screener_returns_items_and_disclaimer(client):
    """Screener with FPT-only universe returns ranked item + disclaimer."""
    r = client.get("/api/v1/screener")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "disclaimer" in data
    assert data["disclaimer"] == DISCLAIMER
    assert isinstance(data["items"], list)
    # Each item has expected fields
    if data["items"]:
        item = data["items"][0]
        assert "ticker" in item
        assert "score" in item
        assert "rank" in item


# ---------------------------------------------------------------------------
# Stock detail
# ---------------------------------------------------------------------------

def test_stock_detail_shape(client):
    r = client.get("/api/v1/stock/FPT")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == "FPT"
    assert "company" in data
    assert "price" in data
    assert "financials" in data
    assert "disclaimer" in data
    assert data["disclaimer"] == DISCLAIMER
    assert data["price"]["current_price"] == 73_500.0
    assert data["company"]["sector"] == "Technology"


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

def test_valuation_returns_reco_and_disclaimer(client):
    r = client.get("/api/v1/valuation/FPT")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == "FPT"
    assert data["recommendation"] in ("BUY", "HOLD", "SELL")
    assert isinstance(data["reasons"], list)
    assert "disclaimer" in data
    assert data["disclaimer"] == DISCLAIMER
    assert isinstance(data["score"], int)
    assert 0 <= data["score"] <= 100


# ---------------------------------------------------------------------------
# CORS origins from env
# ---------------------------------------------------------------------------

def test_cors_origins_from_env():
    """CORS allow_origins are built from CORS_ORIGINS env variable."""
    os.environ["CORS_ORIGINS"] = "http://custom-origin:4000,http://another:5000"
    # Re-import after env change — test the _CORS_ORIGINS list directly
    import importlib
    import backend.api.main as main_mod
    importlib.reload(main_mod)
    assert "http://custom-origin:4000" in main_mod._CORS_ORIGINS
    assert "http://another:5000" in main_mod._CORS_ORIGINS
    # Cleanup
    del os.environ["CORS_ORIGINS"]
    importlib.reload(main_mod)


# ---------------------------------------------------------------------------
# RecommendationLogger — SQLite round-trip
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_logger(tmp_path):
    db_file = tmp_path / "test_reco.db"
    return RecommendationLogger(db_path=str(db_file))


def test_recommendation_logger_round_trip(tmp_logger):
    """Log recommendation → read back → verify fields."""
    rec_id = tmp_logger.log_recommendation(
        ticker="FPT",
        date="2026-06-15",
        recommendation="BUY",
        target_price=85_000.0,
        current_price=73_500.0,
        score=72,
        upside_pct=0.157,
        reasons=["Upside 15.7%", "F-score 7/9"],
    )
    assert rec_id > 0

    rows = tmp_logger.get_recommendations(ticker="FPT")
    assert len(rows) == 1
    r = rows[0]
    assert r["ticker"] == "FPT"
    assert r["recommendation"] == "BUY"
    assert r["score"] == 72
    assert r["reasons"] == ["Upside 15.7%", "F-score 7/9"]


def test_paper_position_open_close_pnl(tmp_logger):
    """Open paper position → close → verify P&L computed correctly."""
    rec_id = tmp_logger.log_recommendation(
        ticker="VCB", date="2026-06-15", recommendation="BUY",
        current_price=80_000.0, score=65,
    )

    pos_id = tmp_logger.open_paper_position(
        ticker="VCB",
        entry_date="2026-06-15",
        entry_price=80_000.0,
        shares=100,
        recommendation_id=rec_id,
    )
    assert pos_id > 0

    ok = tmp_logger.close_paper_position(pos_id, "2026-07-01", exit_price=90_000.0)
    assert ok is True

    portfolio = tmp_logger.get_paper_portfolio(ticker="VCB", status="closed")
    assert len(portfolio) == 1
    pos = portfolio[0]
    assert pos["status"] == "closed"
    assert abs(float(pos["pnl"]) - 1_000_000.0) < 1  # (90k-80k)*100 = 1_000_000


def test_paper_portfolio_open_status(tmp_logger):
    """Open position appears in get_paper_portfolio(status='open')."""
    tmp_logger.log_recommendation(
        ticker="HPG", date="2026-06-15", recommendation="HOLD",
    )
    pos_id = tmp_logger.open_paper_position(
        ticker="HPG", entry_date="2026-06-15", entry_price=25_000.0, shares=200,
    )
    portfolio = tmp_logger.get_paper_portfolio(status="open")
    tickers = [p["ticker"] for p in portfolio]
    assert "HPG" in tickers
