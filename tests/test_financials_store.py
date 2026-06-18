"""Offline tests for FinancialsStore (SQLite backend) + period helpers."""
import tempfile
from pathlib import Path

from data.vn.models import FinancialStatement
from data.vn.financials_store import (
    FinancialsStore,
    latest_period_labels,
    _period_end,
)


def _fake_stmt() -> FinancialStatement:
    return FinancialStatement(
        ticker="FPT",
        statement_type="income_statement",
        period="year",
        items={
            "net_sales": {"2025": 70.0, "2024": 60.0, "2023": 50.0, "2022": 40.0},
            "net_income": {"2025": 9.0, "2024": 7.0, "2023": 6.0},
        },
        labels={"net_sales": "Doanh thu thuần", "net_income": "Lợi nhuận sau thuế"},
    )


def test_latest_period_labels_desc_top_n():
    fs = _fake_stmt()
    assert latest_period_labels(fs, 2) == ["2025", "2024"]
    assert latest_period_labels(fs, 3) == ["2025", "2024", "2023"]


def test_period_end_year_and_quarter():
    assert _period_end("2024", "year") == "2024-12-31"
    assert _period_end("2024-Q3", "quarter") == "2024-09-30"


def test_store_upsert_and_count(tmp_path: Path):
    db = str(tmp_path / "fin.db")
    store = FinancialsStore(db_url=None, sqlite_path=db)
    assert store.backend == "sqlite"
    written = store.store_statement(_fake_stmt(), max_periods=2, source="test")
    assert written == 2                       # 2 most-recent years
    assert store.count() == 2
    # idempotent upsert — same rows, no duplication
    store.store_statement(_fake_stmt(), max_periods=2, source="test")
    assert store.count() == 2


def test_store_empty_statement_writes_nothing(tmp_path: Path):
    store = FinancialsStore(db_url=None, sqlite_path=str(tmp_path / "e.db"))
    empty = FinancialStatement(ticker="X", statement_type="balance_sheet", period="year")
    assert store.store_statement(empty, max_periods=2) == 0
    assert store.count() == 0


def test_set_and_get_shares(tmp_path: Path):
    store = FinancialsStore(db_url=None, sqlite_path=str(tmp_path / "sh.db"))
    assert store.get_shares("VIC") is None          # not collected yet
    store.set_shares("vic", 7_706_000_000.0, source="test")
    assert store.get_shares("VIC") == 7_706_000_000.0  # case-insensitive
    # upsert overwrites
    store.set_shares("VIC", 3_800_000_000.0)
    assert store.get_shares("VIC") == 3_800_000_000.0


def test_set_shares_ignores_nonpositive(tmp_path: Path):
    store = FinancialsStore(db_url=None, sqlite_path=str(tmp_path / "sh2.db"))
    store.set_shares("FPT", 0.0)
    store.set_shares("FPT", -5.0)
    assert store.get_shares("FPT") is None
