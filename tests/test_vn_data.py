"""Tests for data.vn — VN Stock data adapter layer.

Default run (offline, no network): python3 -m pytest tests/test_vn_data.py -q
Live smoke test (single symbol): RUN_LIVE_VNSTOCK=1 python3 -m pytest tests/test_vn_data.py -q -m live
"""

import os
import sqlite3
import time
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pandas as pd
import pytest

from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from data.vn.base import StockDataSource
from data.vn.cache import CachedDataSource
from data.vn.universe import get_universe, get_vn30, is_bank
from data.vn.vnstock_parsers import parse_long_financials, parse_ratio_df


# ---------------------------------------------------------------------------
# Fake source (offline fixture)
# ---------------------------------------------------------------------------

class FakeSource(StockDataSource):
    """Deterministic fake implementing StockDataSource for offline tests.

    get_ohlcv returns one row per month between start and end so tests can
    verify slicing and coverage checks without network access.
    fetch_ranges records every (start, end) pair passed to get_ohlcv.
    """

    def __init__(self, fail_ticker: str = "FAIL"):
        self.fail_ticker = fail_ticker
        self.call_counts: dict = {}
        self.fetch_ranges: list = []  # list of (start, end) tuples passed to get_ohlcv

    def _count(self, method: str):
        self.call_counts[method] = self.call_counts.get(method, 0) + 1

    def get_ohlcv(self, ticker: str, start: str, end: str, interval: str = "1D") -> pd.DataFrame:
        self._count("ohlcv")
        self.fetch_ranges.append((start, end))
        if ticker == self.fail_ticker:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        # Produce one row per month-start within [start, end] for range coverage tests
        dates = pd.date_range(start=start, end=end, freq="MS")
        if dates.empty:
            # Fallback: at least the two canonical rows used by existing tests
            dates = pd.date_range("2024-01-02", periods=2, freq="D")
        rows = [
            {
                "time": ts,
                "open": 48.0, "high": 49.5, "low": 47.5, "close": 49.0,
                "volume": 1_000_000,
            }
            for ts in dates
        ]
        return pd.DataFrame(rows)

    def get_financials(self, ticker: str, statement_type: str, period: str = "year") -> FinancialStatement:
        self._count(f"financials:{statement_type}")
        if ticker == self.fail_ticker:
            return FinancialStatement(ticker=ticker, statement_type=statement_type, period=period)
        return FinancialStatement(
            ticker=ticker,
            statement_type=statement_type,
            period=period,
            items={"current_assets": {"2024": 1.2e12, "2023": 1.1e12}},
            labels={"current_assets": "Tài sản ngắn hạn"},
        )

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        self._count("ratios")
        if ticker == self.fail_ticker:
            return Ratios(ticker=ticker, period=period)
        return Ratios(
            ticker=ticker,
            period=period,
            items={"pe_ratio": {"2024q4": 12.5, "2024q3": 11.8}},
            period_labels=["2024q3", "2024q4"],
        )

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        self._count("company")
        if ticker == self.fail_ticker:
            return None
        return CompanyInfo(
            ticker=ticker,
            organ_name="FPT Corporation",
            organ_short_name="FPT",
            sector="Technology",
            icb_code="9537",
            com_group_code="FPT",
            market_cap=1.5e14,
            current_price=49_000.0,
            issue_share=616_621_596,
            is_bank=False,
            listing_date="2006-12-13",
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_source():
    return FakeSource()


@pytest.fixture
def tmp_cache(tmp_path, fake_source):
    """CachedDataSource with SQLite backend in a temp dir."""
    return CachedDataSource(
        source=fake_source,
        cache_dir=str(tmp_path / "vn_cache"),
        db_url=None,
        ttl={"ohlcv": 60, "financials": 60, "ratios": 60, "company": 60},
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestFinancialStatement:
    def test_get_existing_item(self):
        stmt = FinancialStatement(
            ticker="FPT", statement_type="balance_sheet", period="year",
            items={"current_assets": {"2024": 1.2e12, "2023": 1.1e12}},
            labels={"current_assets": "Tài sản ngắn hạn"},
        )
        assert stmt.get("current_assets", "2024") == pytest.approx(1.2e12)
        assert stmt.get("current_assets", "2023") == pytest.approx(1.1e12)

    def test_get_missing_item_returns_none(self):
        stmt = FinancialStatement(ticker="FPT", statement_type="balance_sheet", period="year")
        assert stmt.get("nonexistent", "2024") is None

    def test_get_missing_period_returns_none(self):
        stmt = FinancialStatement(
            ticker="FPT", statement_type="balance_sheet", period="year",
            items={"current_assets": {"2024": 1.2e12}},
        )
        assert stmt.get("current_assets", "2022") is None

    def test_to_dict_from_dict_roundtrip(self):
        stmt = FinancialStatement(
            ticker="FPT", statement_type="income_statement", period="quarter",
            items={"sales": {"2024Q1": 5e11}},
            labels={"sales": "Doanh thu"},
        )
        d = stmt.to_dict()
        restored = FinancialStatement.from_dict(d)
        assert restored.ticker == "FPT"
        assert restored.statement_type == "income_statement"
        assert restored.period == "quarter"
        assert restored.get("sales", "2024Q1") == pytest.approx(5e11)
        assert restored.labels["sales"] == "Doanh thu"

    def test_empty_statement_serialization(self):
        stmt = FinancialStatement(ticker="ACB", statement_type="cash_flow", period="year")
        restored = FinancialStatement.from_dict(stmt.to_dict())
        assert restored.ticker == "ACB"
        assert restored.items == {}


class TestRatios:
    def test_get_existing_ratio(self):
        r = Ratios(
            ticker="FPT", period="year",
            items={"pe_ratio": {"2024q4": 12.5}},
            period_labels=["2024q4"],
        )
        assert r.get("pe_ratio", "2024q4") == pytest.approx(12.5)

    def test_get_missing_returns_none(self):
        r = Ratios(ticker="FPT", period="year")
        assert r.get("pb_ratio", "2024q4") is None

    def test_to_dict_from_dict_roundtrip(self):
        r = Ratios(
            ticker="FPT", period="quarter",
            items={"roe": {"2024q1": 0.23, "2023q4": 0.21}},
            period_labels=["2023q4", "2024q1"],
        )
        d = r.to_dict()
        restored = Ratios.from_dict(d)
        assert restored.ticker == "FPT"
        assert restored.get("roe", "2024q1") == pytest.approx(0.23)
        assert restored.period_labels == ["2023q4", "2024q1"]


class TestCompanyInfo:
    def test_to_dict_from_dict_roundtrip(self):
        c = CompanyInfo(
            ticker="FPT",
            organ_name="FPT Corporation",
            is_bank=False,
            sector="Technology",
            icb_code="9537",
            market_cap=1.5e14,
        )
        d = c.to_dict()
        restored = CompanyInfo.from_dict(d)
        assert restored.ticker == "FPT"
        assert restored.is_bank is False
        assert restored.sector == "Technology"
        assert restored.market_cap == pytest.approx(1.5e14)

    def test_bank_flag_preserved(self):
        c = CompanyInfo(ticker="VCB", is_bank=True)
        restored = CompanyInfo.from_dict(c.to_dict())
        assert restored.is_bank is True


# ---------------------------------------------------------------------------
# Cache: OHLCV parquet
# ---------------------------------------------------------------------------

class TestOhlcvCache:
    def test_cache_miss_calls_source(self, tmp_cache, fake_source):
        df = tmp_cache.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        assert not df.empty
        assert fake_source.call_counts.get("ohlcv", 0) == 1

    def test_cache_hit_skips_source(self, tmp_cache, fake_source):
        tmp_cache.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        tmp_cache.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        # Source called only once — second call served from cache
        assert fake_source.call_counts.get("ohlcv", 0) == 1

    def test_parquet_roundtrip(self, tmp_cache):
        df1 = tmp_cache.get_ohlcv("FPT", "2024-01-01", "2024-12-31")
        df2 = tmp_cache.get_ohlcv("FPT", "2024-01-01", "2024-12-31")
        pd.testing.assert_frame_equal(df1.reset_index(drop=True), df2.reset_index(drop=True))

    def test_parquet_file_created(self, tmp_cache, tmp_path):
        tmp_cache.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        parquet_path = tmp_path / "vn_cache" / "ohlcv" / "FPT.parquet"
        assert parquet_path.exists()

    def test_ttl_expiry_refetches(self, tmp_path, fake_source):
        # TTL = 0 forces every call to re-fetch
        cached = CachedDataSource(
            source=fake_source,
            cache_dir=str(tmp_path / "vn_cache_ttl"),
            db_url=None,
            ttl={"ohlcv": 0, "financials": 0, "ratios": 0, "company": 0},
        )
        cached.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        cached.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        assert fake_source.call_counts.get("ohlcv", 0) == 2

    def test_empty_result_not_cached(self, tmp_path):
        fail_source = FakeSource(fail_ticker="FPT")
        cached = CachedDataSource(
            source=fail_source,
            cache_dir=str(tmp_path / "vn_cache_empty"),
            db_url=None,
        )
        df = cached.get_ohlcv("FPT", "2024-01-01", "2024-01-31")
        assert df.empty
        parquet_path = tmp_path / "vn_cache_empty" / "ohlcv" / "FPT.parquet"
        assert not parquet_path.exists()


# ---------------------------------------------------------------------------
# Cache: KV (financials, ratios, company) with SQLite
# ---------------------------------------------------------------------------

class TestKvCache:
    def test_financials_cache_miss_then_hit(self, tmp_cache, fake_source):
        tmp_cache.get_financials("FPT", "balance_sheet")
        tmp_cache.get_financials("FPT", "balance_sheet")
        assert fake_source.call_counts.get("financials:balance_sheet", 0) == 1

    def test_financials_roundtrip(self, tmp_cache):
        stmt = tmp_cache.get_financials("FPT", "balance_sheet")
        assert stmt.get("current_assets", "2024") == pytest.approx(1.2e12)
        cached_stmt = tmp_cache.get_financials("FPT", "balance_sheet")
        assert cached_stmt.get("current_assets", "2024") == pytest.approx(1.2e12)

    def test_ratios_cache_miss_then_hit(self, tmp_cache, fake_source):
        tmp_cache.get_ratios("FPT")
        tmp_cache.get_ratios("FPT")
        assert fake_source.call_counts.get("ratios", 0) == 1

    def test_ratios_roundtrip(self, tmp_cache):
        r = tmp_cache.get_ratios("FPT")
        assert r.get("pe_ratio", "2024q4") == pytest.approx(12.5)
        cached_r = tmp_cache.get_ratios("FPT")
        assert cached_r.get("pe_ratio", "2024q4") == pytest.approx(12.5)

    def test_company_cache_miss_then_hit(self, tmp_cache, fake_source):
        tmp_cache.get_company("FPT")
        tmp_cache.get_company("FPT")
        assert fake_source.call_counts.get("company", 0) == 1

    def test_company_roundtrip(self, tmp_cache):
        c = tmp_cache.get_company("FPT")
        assert c is not None
        assert c.ticker == "FPT"
        assert c.is_bank is False
        cached_c = tmp_cache.get_company("FPT")
        assert cached_c.ticker == "FPT"

    def test_company_none_not_cached(self, tmp_path):
        fail_source = FakeSource(fail_ticker="FAIL")
        cached = CachedDataSource(
            source=fail_source,
            cache_dir=str(tmp_path / "vn_cache_none"),
            db_url=None,
        )
        result = cached.get_company("FAIL")
        assert result is None
        # Second call must also hit the source (None not cached)
        result2 = cached.get_company("FAIL")
        assert result2 is None
        assert fail_source.call_counts.get("company", 0) == 2

    def test_different_tickers_isolated(self, tmp_cache):
        stmt_fpt = tmp_cache.get_financials("FPT", "balance_sheet")
        stmt_acb = tmp_cache.get_financials("ACB", "balance_sheet")
        assert stmt_fpt.ticker == "FPT"
        assert stmt_acb.ticker == "ACB"

    def test_different_statement_types_isolated(self, tmp_cache, fake_source):
        tmp_cache.get_financials("FPT", "balance_sheet")
        tmp_cache.get_financials("FPT", "income_statement")
        assert fake_source.call_counts.get("financials:balance_sheet", 0) == 1
        assert fake_source.call_counts.get("financials:income_statement", 0) == 1

    def test_kv_ttl_expiry(self, tmp_path, fake_source):
        cached = CachedDataSource(
            source=fake_source,
            cache_dir=str(tmp_path / "vn_cache_kv_ttl"),
            db_url=None,
            ttl={"ohlcv": 0, "financials": 0, "ratios": 0, "company": 0},
        )
        cached.get_ratios("FPT")
        cached.get_ratios("FPT")
        assert fake_source.call_counts.get("ratios", 0) == 2


# ---------------------------------------------------------------------------
# Universe tests
# ---------------------------------------------------------------------------

class TestUniverse:
    def test_vn30_returns_30_tickers(self):
        tickers = get_universe("VN30")
        assert len(tickers) == 30

    def test_vn30_contains_expected_tickers(self):
        tickers = get_universe("VN30")
        for expected in ["FPT", "VCB", "MBB", "HPG", "VIC"]:
            assert expected in tickers

    def test_get_vn30_shortcut(self):
        assert get_vn30() == get_universe("VN30")

    def test_unknown_universe_raises(self):
        with pytest.raises(ValueError, match="Unknown universe"):
            get_universe("SP500")

    def test_config_override(self):
        override = {"MINI": ["FPT", "VCB"]}
        tickers = get_universe("MINI", config_override=override)
        assert tickers == ["FPT", "VCB"]

    def test_is_bank_known_banks(self):
        for ticker in ["VCB", "MBB", "ACB", "TCB", "BID"]:
            assert is_bank(ticker), f"{ticker} should be detected as bank"

    def test_is_bank_non_banks(self):
        for ticker in ["FPT", "VIC", "HPG", "MSN"]:
            assert not is_bank(ticker), f"{ticker} should NOT be detected as bank"

    def test_no_duplicates_in_vn30(self):
        tickers = get_universe("VN30")
        assert len(tickers) == len(set(tickers))


# ---------------------------------------------------------------------------
# Graceful degradation (fail ticker returns empty, no crash)
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    def test_ohlcv_empty_on_fail(self, tmp_cache):
        df = tmp_cache.get_ohlcv("FAIL", "2024-01-01", "2024-12-31")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_financials_empty_on_fail(self, tmp_cache):
        stmt = tmp_cache.get_financials("FAIL", "balance_sheet")
        assert isinstance(stmt, FinancialStatement)
        assert stmt.items == {}

    def test_ratios_empty_on_fail(self, tmp_cache):
        r = tmp_cache.get_ratios("FAIL")
        assert isinstance(r, Ratios)
        assert r.items == {}

    def test_company_none_on_fail(self, tmp_cache):
        c = tmp_cache.get_company("FAIL")
        assert c is None


# ---------------------------------------------------------------------------
# Parser unit tests (pure, no network) — vnstock_parsers module
# ---------------------------------------------------------------------------

class TestParseLongFinancials:
    """Unit tests for parse_long_financials using in-memory fixture DataFrames."""

    def _make_df(self):
        """Minimal long-format financial DataFrame mimicking vnstock output."""
        return pd.DataFrame([
            {"item": "Tài sản ngắn hạn", "item_en": "Current Assets", "item_id": "current_assets",
             "2024": 1.2e12, "2023": 1.1e12, "2022": 1.0e12},
            {"item": "Tiền và tương đương tiền", "item_en": "Cash", "item_id": "cash",
             "2024": 3.0e11, "2023": 2.5e11, "2022": 2.0e11},
            {"item": "",  "item_en": "", "item_id": "",  # blank item_id → must be skipped
             "2024": 0.0, "2023": 0.0, "2022": 0.0},
        ])

    def test_items_populated(self):
        df = self._make_df()
        stmt = parse_long_financials(df, "FPT", "balance_sheet", "year")
        assert "current_assets" in stmt.items
        assert "cash" in stmt.items

    def test_values_correct(self):
        df = self._make_df()
        stmt = parse_long_financials(df, "FPT", "balance_sheet", "year")
        assert stmt.get("current_assets", "2024") == pytest.approx(1.2e12)
        assert stmt.get("cash", "2023") == pytest.approx(2.5e11)

    def test_labels_populated(self):
        df = self._make_df()
        stmt = parse_long_financials(df, "FPT", "balance_sheet", "year")
        assert stmt.labels["current_assets"] == "Tài sản ngắn hạn"

    def test_blank_item_id_skipped(self):
        df = self._make_df()
        stmt = parse_long_financials(df, "FPT", "balance_sheet", "year")
        # Blank item_id row should not appear as an empty-string key
        assert "" not in stmt.items

    def test_none_df_returns_empty(self):
        stmt = parse_long_financials(None, "FPT", "balance_sheet", "year")
        assert stmt.items == {}

    def test_empty_df_returns_empty(self):
        stmt = parse_long_financials(pd.DataFrame(), "FPT", "balance_sheet", "year")
        assert stmt.items == {}

    def test_non_numeric_value_skipped(self):
        df = pd.DataFrame([
            {"item": "Item A", "item_en": "", "item_id": "item_a",
             "2024": "N/A", "2023": 5.0e11},
        ])
        stmt = parse_long_financials(df, "FPT", "balance_sheet", "year")
        # "N/A" must be skipped; 2023 value must be present
        assert "2024" not in stmt.items.get("item_a", {})
        assert stmt.get("item_a", "2023") == pytest.approx(5.0e11)

    def test_metadata_fields_set(self):
        df = self._make_df()
        stmt = parse_long_financials(df, "ACB", "income_statement", "quarter")
        assert stmt.ticker == "ACB"
        assert stmt.statement_type == "income_statement"
        assert stmt.period == "quarter"


class TestParseRatioDf:
    """Unit tests for parse_ratio_df using in-memory fixture DataFrames."""

    def _make_ratio_df(self):
        """Minimal transposed ratio DataFrame mimicking vnstock 4.0.4 output.

        Columns: item, item_en, item_id, <data col 0>, <data col 1>
        Row 0: item_id='year'   → year values
        Row 1: item_id='quarter' → quarter values
        Row 2+: actual metrics
        """
        cols = ["item", "item_en", "item_id", "val_a", "val_b"]
        data = [
            # year row
            ["Year", "Year", "year",    2024,  2024],
            # quarter row
            ["Quarter", "Quarter", "quarter", 3, 4],
            # metric rows
            ["P/E", "PE Ratio",  "pe_ratio",  11.8, 12.5],
            ["P/B", "PB Ratio",  "pb_ratio",   1.5,  1.6],
            # metadata row that must be skipped
            ["Ratio Type", "", "ratioType", "FINANCIAL", "FINANCIAL"],
        ]
        return pd.DataFrame(data, columns=cols)

    def test_period_labels_built(self):
        df = self._make_ratio_df()
        r = parse_ratio_df(df, "FPT", "year")
        assert r.period_labels == ["2024q3", "2024q4"]

    def test_metric_values_correct(self):
        df = self._make_ratio_df()
        r = parse_ratio_df(df, "FPT", "year")
        assert r.get("pe_ratio", "2024q3") == pytest.approx(11.8)
        assert r.get("pe_ratio", "2024q4") == pytest.approx(12.5)
        assert r.get("pb_ratio", "2024q4") == pytest.approx(1.6)

    def test_metadata_rows_skipped(self):
        df = self._make_ratio_df()
        r = parse_ratio_df(df, "FPT", "year")
        assert "ratioType" not in r.items
        assert "year" not in r.items
        assert "quarter" not in r.items

    def test_none_df_returns_empty(self):
        r = parse_ratio_df(None, "FPT", "year")
        assert r.items == {}
        assert r.period_labels == []

    def test_empty_df_returns_empty(self):
        r = parse_ratio_df(pd.DataFrame(), "FPT", "year")
        assert r.items == {}

    def test_bad_year_quarter_falls_back_to_col_label(self):
        cols = ["item", "item_en", "item_id", "val_a"]
        data = [
            ["Year", "Year", "year", "bad"],
            ["Quarter", "Quarter", "quarter", "bad"],
            ["P/E", "PE Ratio", "pe_ratio", 12.0],
        ]
        df = pd.DataFrame(data, columns=cols)
        r = parse_ratio_df(df, "FPT", "year")
        # Falls back to "col3" label
        assert r.period_labels == ["col3"]
        assert r.get("pe_ratio", "col3") == pytest.approx(12.0)

    def test_metadata_fields_set(self):
        df = self._make_ratio_df()
        r = parse_ratio_df(df, "VCB", "quarter")
        assert r.ticker == "VCB"
        assert r.period == "quarter"


# ---------------------------------------------------------------------------
# Cache: OHLCV wide-window strategy (C1)
# ---------------------------------------------------------------------------

class TestOhlcvWideWindowCache:
    """Verify that the cache fetches a wide window on MISS and serves narrow requests from it."""

    def _make_cache(self, tmp_path, fake_source, history_start="2020-01-01", ttl=3600):
        return CachedDataSource(
            source=fake_source,
            cache_dir=str(tmp_path / "vn_cache"),
            db_url=None,
            ttl={"ohlcv": ttl, "financials": ttl, "ratios": ttl, "company": ttl},
            history_start=history_start,
        )

    def test_first_call_fetches_wide_window(self, tmp_path, fake_source):
        cache = self._make_cache(tmp_path, fake_source, history_start="2020-01-01")
        cache.get_ohlcv("FPT", "2024-01-01", "2024-03-31")
        # Source must have been called exactly once
        assert fake_source.call_counts.get("ohlcv", 0) == 1
        # The fetched window start must be history_start, not the requested start
        fetched_start, fetched_end = fake_source.fetch_ranges[0]
        assert fetched_start == "2020-01-01"

    def test_narrow_then_wider_is_cache_hit(self, tmp_path, fake_source):
        """Cache wide window, then request a wider-but-still-covered sub-range → HIT."""
        cache = self._make_cache(tmp_path, fake_source, history_start="2018-01-01")
        # First call: populates wide cache [2018-01-01, today]
        cache.get_ohlcv("FPT", "2024-01-01", "2024-06-30")
        assert fake_source.call_counts.get("ohlcv", 0) == 1
        # Second call: wider range still within cached window → HIT, no new fetch
        cache.get_ohlcv("FPT", "2022-01-01", "2024-12-31")
        assert fake_source.call_counts.get("ohlcv", 0) == 1, (
            "Second request should be served from cache — source must NOT be called again"
        )

    def test_wide_then_narrow_returns_sliced_data(self, tmp_path, fake_source):
        """Cache populated with wide window; narrow request returns only matching rows."""
        cache = self._make_cache(tmp_path, fake_source, history_start="2020-01-01")
        # Populate cache
        cache.get_ohlcv("FPT", "2024-01-01", "2024-12-31")
        fake_source.call_counts.clear()

        # Narrow request — must come from cache (source NOT called)
        df = cache.get_ohlcv("FPT", "2024-03-01", "2024-05-31")
        assert fake_source.call_counts.get("ohlcv", 0) == 0, "Narrow request must be a cache HIT"
        # All returned rows must be within the requested window
        if not df.empty:
            assert df["time"].min() >= pd.Timestamp("2024-03-01")
            assert df["time"].max() <= pd.Timestamp("2024-05-31")

    def test_request_outside_cached_window_triggers_refetch(self, tmp_path, fake_source):
        """Request a date before history_start → cache MISS, refetch wide window."""
        cache = self._make_cache(tmp_path, fake_source, history_start="2022-01-01")
        # Populate cache with [2022-01-01, today]
        cache.get_ohlcv("FPT", "2023-01-01", "2023-12-31")
        assert fake_source.call_counts.get("ohlcv", 0) == 1

        # Request that extends BEFORE cached window start → MISS
        cache.get_ohlcv("FPT", "2019-01-01", "2023-12-31")
        assert fake_source.call_counts.get("ohlcv", 0) == 2, (
            "Request outside cached window must trigger a refetch"
        )

    def test_returned_df_sliced_to_requested_range(self, tmp_path, fake_source):
        """Wide fetch stores everything; return value contains only requested rows."""
        cache = self._make_cache(tmp_path, fake_source, history_start="2015-01-01")
        df = cache.get_ohlcv("FPT", "2024-06-01", "2024-08-31")
        if not df.empty:
            assert df["time"].min() >= pd.Timestamp("2024-06-01")
            assert df["time"].max() <= pd.Timestamp("2024-08-31")


# ---------------------------------------------------------------------------
# Cache: corrupt KV row treated as MISS (M5)
# ---------------------------------------------------------------------------

class TestKvCorruptRowMiss:
    def test_corrupt_payload_treated_as_miss(self, tmp_path, fake_source):
        """A corrupt JSON row in the KV store must be treated as a MISS, not crash."""
        cache = CachedDataSource(
            source=fake_source,
            cache_dir=str(tmp_path / "vn_cache_corrupt"),
            db_url=None,
            ttl={"ohlcv": 3600, "financials": 3600, "ratios": 3600, "company": 3600},
        )
        # Prime a valid entry
        cache.get_ratios("FPT")
        assert fake_source.call_counts.get("ratios", 0) == 1

        # Corrupt the row directly in SQLite
        db_path = tmp_path / "vn_cache_corrupt" / "vn_cache.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("UPDATE vn_cache SET payload = 'NOT_VALID_JSON' WHERE cache_key = 'FPT:ratios:year'")
        conn.commit()
        conn.close()

        # Next read must treat the corrupt row as a MISS and refetch
        result = cache.get_ratios("FPT")
        assert fake_source.call_counts.get("ratios", 0) == 2, (
            "Corrupt cache row must trigger a refetch"
        )
        assert result.ticker == "FPT"
        assert result.items != {}


# ---------------------------------------------------------------------------
# Live smoke test (skipped unless RUN_LIVE_VNSTOCK=1)
# ---------------------------------------------------------------------------

_LIVE = os.environ.get("RUN_LIVE_VNSTOCK", "0") == "1"


@pytest.mark.skipif(not _LIVE, reason="Set RUN_LIVE_VNSTOCK=1 to run live tests")
@pytest.mark.live
class TestLiveVnstock:
    """Single-symbol live smoke test — only runs with RUN_LIVE_VNSTOCK=1.

    Rate-limit safe: one symbol, calls spaced by VnstockSource throttle.
    """

    def test_ohlcv_fpt(self, tmp_path):
        from data.vn.vnstock_source import VnstockSource
        src = VnstockSource(throttle_seconds=3.5)
        df = src.get_ohlcv("FPT", "2025-06-01", "2026-06-13")
        assert not df.empty
        assert set(["time", "open", "high", "low", "close", "volume"]).issubset(df.columns)
        assert df["close"].iloc[-1] > 0

    def test_financials_fpt(self):
        from data.vn.vnstock_source import VnstockSource
        src = VnstockSource(throttle_seconds=3.5)
        stmt = src.get_financials("FPT", "balance_sheet", period="year")
        assert stmt.ticker == "FPT"
        assert len(stmt.items) > 0

    def test_ratios_fpt(self):
        from data.vn.vnstock_source import VnstockSource
        src = VnstockSource(throttle_seconds=3.5)
        ratios = src.get_ratios("FPT", period="year")
        assert ratios.ticker == "FPT"
        assert "pe_ratio" in ratios.items

    def test_company_fpt(self):
        from data.vn.vnstock_source import VnstockSource
        src = VnstockSource(throttle_seconds=3.5)
        company = src.get_company("FPT")
        assert company is not None
        assert company.ticker == "FPT"
        assert company.is_bank is False
        assert company.sector != ""
