"""Offline tests for the screener package.

Run: python3 -m pytest tests/test_screener.py -q
No network access. All data is served by ScreenerFakeSource.

Live smoke test: RUN_LIVE_VNSTOCK=1 python3 -m pytest tests/test_screener.py -m live -q
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pytest

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from screener.filters.fundamental import (
    _latest_ratio,
    filter_debt_to_equity,
    filter_eps_growth,
    filter_net_margin,
    filter_pe_ratio,
    filter_revenue_growth,
    filter_roe,
)
from screener.engine import _sector_median_pe
from screener.filters.technical import (
    filter_liquidity,
    filter_price_above_ma,
    filter_relative_strength,
)
from screener.scorer import CriterionResult, WatchlistItem, compute_scores, rank_watchlist
from screener import ScreenerEngine

# ---------------------------------------------------------------------------
# Config path (relative to repo root; pytest pythonpath=["."])
# ---------------------------------------------------------------------------
CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "screener.yaml")

# ---------------------------------------------------------------------------
# FakeSource — deterministic offline fixture
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int, close: float, volume: int = 2_000_000) -> pd.DataFrame:
    """Build a synthetic OHLCV DataFrame with n rows."""
    dates = pd.date_range("2023-01-02", periods=n, freq="B")
    return pd.DataFrame({
        "time": dates,
        "open": close * 0.99,
        "high": close * 1.01,
        "low": close * 0.98,
        "close": close,
        "volume": volume,
    })


class ScreenerFakeSource(StockDataSource):
    """Deterministic fake source for 3 tickers: FPT (non-bank), VCB (bank), WEAK (poor FA).

    FPT  — strong FA+TA, should rank #1.
    VCB  — bank, D/E skipped; decent metrics.
    WEAK — fails ROE, EPS growth, revenue growth; should rank last.
    """

    FIXTURES = {
        "FPT": {
            "is_bank": False,
            "sector": "Technology",
            "close": 73.5,        # thousands VND
            "volume": 5_000_000,
            "ratios": {
                "roe":            {"2024q4": 0.25},
                "pe_ratio":       {"2024q4": 18.0},
                "debt_to_equity": {"2024q4": 0.4},
                "net_margin":     {"2024q4": 0.12},
            },
            "income": {
                "eps_basic_vnd":         {"2024": 5_000.0, "2023": 4_000.0},
                "net_sales":             {"2024": 60e12,   "2023": 50e12},
                "net_profit_loss_after_tax": {"2024": 7e12, "2023": 5e12},
            },
        },
        "VCB": {
            "is_bank": True,
            "sector": "Banks",
            "close": 61.6,
            "volume": 8_000_000,
            "ratios": {
                "roe":            {"2024q4": 0.20},
                "pe_ratio":       {"2024q4": 14.0},
                "debt_to_equity": {"2024q4": 8.0},   # high but skipped for banks
                "net_margin":     {"2024q4": 0.30},
            },
            "income": {
                "eps_basic_vnd":          {"2024": 4_500.0, "2023": 3_800.0},
                "total_operating_income": {"2024": 55e12,   "2023": 48e12},
                "net_profit_loss_after_tax": {"2024": 20e12, "2023": 16e12},
            },
        },
        "WEAK": {
            "is_bank": False,
            "sector": "Technology",
            "close": 10.0,
            "volume": 500_000,
            "ratios": {
                "roe":            {"2024q4": 0.05},  # fails ROE > 15%
                "pe_ratio":       {"2024q4": 40.0},  # fails P/E < 25
                "debt_to_equity": {"2024q4": 2.5},   # fails D/E < 1.0
                "net_margin":     {"2024q4": 0.02},  # fails net_margin > 5%
            },
            "income": {
                "eps_basic_vnd": {"2024": 800.0,  "2023": 1_000.0},  # declining EPS
                "net_sales":     {"2024": 10e12,  "2023": 12e12},     # declining revenue
                "net_profit_loss_after_tax": {"2024": 1e12, "2023": 1.5e12},
            },
        },
    }

    def get_ohlcv(self, ticker: str, start: str, end: str, interval: str = "1D") -> pd.DataFrame:
        if ticker == "VNINDEX":
            return _make_ohlcv(300, close=1250.0, volume=500_000_000)
        if ticker not in self.FIXTURES:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        f = self.FIXTURES[ticker]
        return _make_ohlcv(300, close=f["close"], volume=f["volume"])

    def get_financials(self, ticker: str, statement_type: str, period: str = "year") -> FinancialStatement:
        if ticker not in self.FIXTURES or statement_type != "income_statement":
            return FinancialStatement(ticker=ticker, statement_type=statement_type, period=period)
        return FinancialStatement(
            ticker=ticker,
            statement_type=statement_type,
            period=period,
            items=self.FIXTURES[ticker]["income"],
        )

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        if ticker not in self.FIXTURES:
            return Ratios(ticker=ticker, period=period)
        return Ratios(
            ticker=ticker,
            period=period,
            items=self.FIXTURES[ticker]["ratios"],
            period_labels=["2024q4"],
        )

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        if ticker not in self.FIXTURES:
            return None
        f = self.FIXTURES[ticker]
        return CompanyInfo(
            ticker=ticker,
            organ_name=ticker,
            sector=f["sector"],
            icb_code="9999",
            market_cap=100e12,
            current_price=f["close"] * 1000,
            is_bank=f["is_bank"],
        )


@pytest.fixture
def fake_src():
    return ScreenerFakeSource()


# ---------------------------------------------------------------------------
# FA filter tests
# ---------------------------------------------------------------------------

class TestFundamentalFilters:
    def _ratios(self, ticker: str, data: dict) -> Ratios:
        return Ratios(ticker=ticker, period="year", items=data, period_labels=["2024q4"])

    def _income(self, ticker: str, data: dict) -> FinancialStatement:
        return FinancialStatement(ticker=ticker, statement_type="income_statement",
                                  period="year", items=data)

    # ROE
    def test_roe_pass(self):
        r = self._ratios("FPT", {"roe": {"2024q4": 0.20}})
        passed, value, _ = filter_roe(r, threshold=0.15)
        assert passed is True
        assert value == pytest.approx(0.20)

    def test_roe_fail(self):
        r = self._ratios("X", {"roe": {"2024q4": 0.10}})
        passed, _, _ = filter_roe(r, threshold=0.15)
        assert passed is False

    def test_roe_na(self):
        r = Ratios(ticker="X", period="year")
        passed, value, _ = filter_roe(r, threshold=0.15)
        assert value is None

    # P/E
    def test_pe_pass_below_both(self):
        r = self._ratios("X", {"pe_ratio": {"2024q4": 18.0}})
        passed, value, _ = filter_pe_ratio(r, threshold=25.0, sector_median=22.0)
        assert passed is True
        assert value == pytest.approx(18.0)

    def test_pe_fail_above_threshold(self):
        r = self._ratios("X", {"pe_ratio": {"2024q4": 30.0}})
        passed, _, _ = filter_pe_ratio(r, threshold=25.0, sector_median=28.0)
        assert passed is False

    def test_pe_fail_above_sector_median(self):
        r = self._ratios("X", {"pe_ratio": {"2024q4": 20.0}})
        passed, _, _ = filter_pe_ratio(r, threshold=25.0, sector_median=18.0)
        assert passed is False

    def test_pe_no_sector_median_uses_threshold_only(self):
        r = self._ratios("X", {"pe_ratio": {"2024q4": 20.0}})
        passed, _, _ = filter_pe_ratio(r, threshold=25.0, sector_median=None)
        assert passed is True

    def test_pe_negative_fails(self):
        r = self._ratios("X", {"pe_ratio": {"2024q4": -5.0}})
        passed, _, _ = filter_pe_ratio(r, threshold=25.0, sector_median=None)
        assert passed is False

    def test_pe_na(self):
        r = Ratios(ticker="X", period="year")
        passed, value, _ = filter_pe_ratio(r, threshold=25.0, sector_median=None)
        assert value is None

    # EPS growth
    def test_eps_growth_pass(self):
        inc = self._income("X", {"eps_basic_vnd": {"2024": 5000.0, "2023": 4000.0}})
        passed, value, _ = filter_eps_growth(inc)
        assert passed is True
        assert value == pytest.approx(0.25)

    def test_eps_growth_fail_decline(self):
        inc = self._income("X", {"eps_basic_vnd": {"2024": 800.0, "2023": 1000.0}})
        passed, value, _ = filter_eps_growth(inc)
        assert passed is False
        assert value == pytest.approx(-0.20)

    def test_eps_growth_fallback_to_net_profit(self):
        inc = self._income("X", {"net_profit_loss_after_tax": {"2024": 10e12, "2023": 8e12}})
        passed, value, _ = filter_eps_growth(inc)
        assert passed is True
        assert value == pytest.approx(0.25)

    def test_eps_growth_na_only_one_period(self):
        inc = self._income("X", {"eps_basic_vnd": {"2024": 5000.0}})
        passed, value, _ = filter_eps_growth(inc)
        assert value is None

    # Revenue growth
    def test_revenue_growth_nonbank_pass(self):
        inc = self._income("X", {"net_sales": {"2024": 60e12, "2023": 50e12}})
        passed, value, _ = filter_revenue_growth(inc, is_bank=False)
        assert passed is True
        assert value == pytest.approx(0.20)

    def test_revenue_growth_bank_uses_operating_income(self):
        inc = self._income("VCB", {"total_operating_income": {"2024": 55e12, "2023": 48e12}})
        passed, value, _ = filter_revenue_growth(inc, is_bank=True)
        assert passed is True

    def test_revenue_growth_fail(self):
        inc = self._income("X", {"net_sales": {"2024": 10e12, "2023": 12e12}})
        passed, _, _ = filter_revenue_growth(inc, is_bank=False)
        assert passed is False

    def test_revenue_growth_na_missing_key(self):
        inc = FinancialStatement(ticker="X", statement_type="income_statement", period="year")
        passed, value, _ = filter_revenue_growth(inc, is_bank=False)
        assert value is None

    # D/E
    def test_de_pass(self):
        r = self._ratios("X", {"debt_to_equity": {"2024q4": 0.5}})
        passed, value, _ = filter_debt_to_equity(r, is_bank=False, threshold=1.0)
        assert passed is True
        assert value == pytest.approx(0.5)

    def test_de_fail(self):
        r = self._ratios("X", {"debt_to_equity": {"2024q4": 2.5}})
        passed, _, _ = filter_debt_to_equity(r, is_bank=False, threshold=1.0)
        assert passed is False

    def test_de_skipped_for_bank(self):
        r = self._ratios("VCB", {"debt_to_equity": {"2024q4": 10.0}})
        passed, value, label = filter_debt_to_equity(r, is_bank=True, threshold=1.0)
        # Bank: passed=True, value=None (N/A), label contains "skipped"
        assert passed is True
        assert value is None
        assert "bank" in label.lower() or "skip" in label.lower()

    def test_de_na(self):
        r = Ratios(ticker="X", period="year")
        passed, value, _ = filter_debt_to_equity(r, is_bank=False, threshold=1.0)
        assert value is None

    # Net margin
    def test_net_margin_pass(self):
        r = self._ratios("X", {"net_margin": {"2024q4": 0.12}})
        passed, value, _ = filter_net_margin(r, threshold=0.05)
        assert passed is True

    def test_net_margin_fail(self):
        r = self._ratios("X", {"net_margin": {"2024q4": 0.02}})
        passed, _, _ = filter_net_margin(r, threshold=0.05)
        assert passed is False

    def test_net_margin_na(self):
        r = Ratios(ticker="X", period="year")
        passed, value, _ = filter_net_margin(r, threshold=0.05)
        assert value is None


# ---------------------------------------------------------------------------
# TA filter tests
# ---------------------------------------------------------------------------

class TestTechnicalFilters:
    # Price > MA
    def test_price_above_ma_pass(self):
        # First 200 bars close=100; next 49 bars close=105; final bar close=110.
        # MA50 = mean of last 50 bars = (49*105 + 110)/50 = 105.1 < 110 ✓
        # MA200 = mean of last 200 bars = (151*100 + 49*105 + 110)/200 ≈ 101.4 < 110 ✓
        base = [{"time": pd.Timestamp("2023-01-02") + pd.Timedelta(days=i),
                 "open": 100.0, "high": 101.0, "low": 99.0,
                 "close": 100.0, "volume": 1_000_000}
                for i in range(200)]
        mid = [{"time": pd.Timestamp("2023-01-02") + pd.Timedelta(days=200 + i),
                "open": 105.0, "high": 106.0, "low": 104.0,
                "close": 105.0, "volume": 1_000_000}
               for i in range(49)]
        last = [{"time": pd.Timestamp("2023-01-02") + pd.Timedelta(days=249),
                 "open": 110.0, "high": 111.0, "low": 109.0,
                 "close": 110.0, "volume": 1_000_000}]
        df = pd.DataFrame(base + mid + last)
        passed, value, _ = filter_price_above_ma(df, ma50_period=50, ma200_period=200)
        assert passed is True
        assert value is not None and value > 1.0  # price > MA200

    def test_price_above_ma_fail_below_ma200(self):
        # Build a declining series: first 200 high, last 50 low → price below MA200
        high = pd.DataFrame({
            "time": pd.date_range("2023-01-02", periods=200, freq="B"),
            "open": 120.0, "high": 122.0, "low": 118.0, "close": 120.0, "volume": 1_000_000,
        })
        low = pd.DataFrame({
            "time": pd.date_range("2023-01-02", periods=50, freq="B").shift(200),
            "open": 80.0, "high": 82.0, "low": 78.0, "close": 80.0, "volume": 1_000_000,
        })
        df = pd.concat([high, low], ignore_index=True)
        passed, _, _ = filter_price_above_ma(df, ma50_period=50, ma200_period=200)
        assert passed is False

    def test_price_above_ma_na_insufficient_history(self):
        df = _make_ohlcv(100, close=50.0)  # only 100 bars, need 200 for MA200
        passed, value, _ = filter_price_above_ma(df, ma50_period=50, ma200_period=200)
        assert value is None

    def test_price_above_ma_na_empty(self):
        df = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        passed, value, _ = filter_price_above_ma(df)
        assert value is None

    # Relative strength
    def test_rs_pass_outperforms_index(self):
        # Ticker up 20%, index flat
        ticker_df = _make_ohlcv(100, close=120.0)
        # First 40 rows close=100, last 60 rows close=120 → return > 0
        rows = [{"time": pd.Timestamp("2023-01-02") + pd.Timedelta(days=i),
                 "open": 100.0, "high": 101.0, "low": 99.0,
                 "close": 100.0 if i < 40 else 120.0, "volume": 1_000_000}
                for i in range(100)]
        ticker_df = pd.DataFrame(rows)
        index_df = _make_ohlcv(100, close=100.0)
        passed, value, _ = filter_relative_strength(ticker_df, index_df, lookback_days=60)
        assert passed is True
        assert value > 0

    def test_rs_fail_underperforms(self):
        # Ticker flat, index up
        rows = [{"time": pd.Timestamp("2023-01-02") + pd.Timedelta(days=i),
                 "open": 100.0, "high": 101.0, "low": 99.0,
                 "close": 100.0 if i < 40 else 80.0, "volume": 1_000_000}
                for i in range(100)]
        ticker_df = pd.DataFrame(rows)
        index_df = _make_ohlcv(100, close=100.0)
        passed, value, _ = filter_relative_strength(ticker_df, index_df, lookback_days=60)
        assert passed is False

    def test_rs_na_no_index(self):
        df = _make_ohlcv(100, close=50.0)
        passed, value, _ = filter_relative_strength(df, index_ohlcv=None, lookback_days=60)
        assert value is None

    def test_rs_na_empty_ticker(self):
        df = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        index_df = _make_ohlcv(100, close=1200.0)
        passed, value, _ = filter_relative_strength(df, index_df, lookback_days=60)
        assert value is None

    # Liquidity
    def test_liquidity_pass(self):
        # close=73.5 * 1000 * 5_000_000 = 367.5 tỷ >> 10 tỷ
        df = _make_ohlcv(30, close=73.5, volume=5_000_000)
        passed, value, _ = filter_liquidity(df, threshold=10_000_000_000, lookback_days=20)
        assert passed is True
        assert value == pytest.approx(73.5 * 1000 * 5_000_000)

    def test_liquidity_fail(self):
        # close=1.0 * 1000 * 100 = 100_000 VND << 10 tỷ
        df = _make_ohlcv(30, close=1.0, volume=100)
        passed, _, _ = filter_liquidity(df, threshold=10_000_000_000, lookback_days=20)
        assert passed is False

    def test_liquidity_na_insufficient_bars(self):
        df = _make_ohlcv(5, close=50.0)  # only 5 bars, need 20
        passed, value, _ = filter_liquidity(df, threshold=10_000_000_000, lookback_days=20)
        assert value is None


# ---------------------------------------------------------------------------
# Scorer tests
# ---------------------------------------------------------------------------

class TestScorer:
    def _make_criteria(self, ticker: str, values: dict, weight: float = 1.0) -> list:
        return [
            CriterionResult(key=k, label=k, passed=(v is not None and v > 0.5),
                            value=v, weight=weight)
            for k, v in values.items()
        ]

    def test_normalise_single_ticker_scores_50(self):
        """Single ticker: min == max → normalised to 0.5 → score = 50."""
        criteria = {"roe": 0.25}
        per_ticker = {"FPT": self._make_criteria("FPT", criteria)}
        scores = compute_scores(per_ticker)
        assert scores["FPT"] == pytest.approx(50.0)

    def test_higher_value_scores_higher(self):
        """Ticker with higher ROE must score above one with lower ROE."""
        per_ticker = {
            "A": [CriterionResult("roe", "ROE", True, 0.30, 1.0)],
            "B": [CriterionResult("roe", "ROE", False, 0.10, 1.0)],
        }
        scores = compute_scores(per_ticker)
        assert scores["A"] > scores["B"]

    def test_na_criterion_excluded_from_score(self):
        """N/A value must not contribute to score but must not crash."""
        per_ticker = {
            "A": [
                CriterionResult("roe", "ROE", True,  0.25, 1.0),
                CriterionResult("de",  "D/E", False, None,  1.0),  # N/A
            ],
        }
        scores = compute_scores(per_ticker)
        # Score must still be computed (not 0, not crash)
        assert 0.0 <= scores["A"] <= 100.0

    def test_all_na_scores_zero(self):
        per_ticker = {
            "A": [CriterionResult("roe", "ROE", False, None, 1.0)],
        }
        scores = compute_scores(per_ticker)
        assert scores["A"] == pytest.approx(0.0)

    def test_ranking_descending(self):
        per_ticker = {
            "A": [CriterionResult("roe", "ROE", True, 0.30, 1.0)],
            "B": [CriterionResult("roe", "ROE", True, 0.20, 1.0)],
            "C": [CriterionResult("roe", "ROE", False, 0.05, 1.0)],
        }
        watchlist = rank_watchlist(per_ticker)
        assert watchlist[0].ticker == "A"
        assert watchlist[1].ticker == "B"
        assert watchlist[2].ticker == "C"
        assert watchlist[0].rank == 1
        assert watchlist[2].rank == 3

    def test_ranking_ties_broken_alphabetically(self):
        per_ticker = {
            "Z": [CriterionResult("roe", "ROE", True, 0.20, 1.0)],
            "A": [CriterionResult("roe", "ROE", True, 0.20, 1.0)],
        }
        watchlist = rank_watchlist(per_ticker)
        assert watchlist[0].ticker == "A"  # alphabetical tie-break
        assert watchlist[1].ticker == "Z"

    def test_watchlist_item_breakdown(self):
        criteria = [
            CriterionResult("roe", "ROE > 15%", True, 0.25, 2.0),
            CriterionResult("de",  "D/E < 1.0", False, 1.5,  1.0),
        ]
        item = WatchlistItem(ticker="FPT", score=75.0, rank=1, criteria=criteria)
        bd = item.breakdown()
        assert len(bd) == 2
        assert bd[0] == ("ROE > 15%", True, 0.25)
        assert bd[1] == ("D/E < 1.0", False, 1.5)
        assert item.passed_count == 1
        assert item.na_count == 0


# ---------------------------------------------------------------------------
# Engine end-to-end tests
# ---------------------------------------------------------------------------

class TestScreenerEngineE2E:
    def test_screen_returns_all_tickers(self, fake_src):
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        watchlist = engine.screen(["FPT", "VCB", "WEAK"])
        assert len(watchlist) == 3

    def test_ranks_are_sequential(self, fake_src):
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        watchlist = engine.screen(["FPT", "VCB", "WEAK"])
        ranks = [item.rank for item in watchlist]
        assert sorted(ranks) == list(range(1, len(watchlist) + 1))

    def test_fpt_ranks_above_weak(self, fake_src):
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        watchlist = engine.screen(["FPT", "WEAK"])
        ticker_order = [item.ticker for item in watchlist]
        assert ticker_order.index("FPT") < ticker_order.index("WEAK")

    def test_each_item_has_criteria_breakdown(self, fake_src):
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        watchlist = engine.screen(["FPT", "VCB"])
        for item in watchlist:
            assert len(item.criteria) > 0
            assert all(hasattr(c, "passed") for c in item.criteria)

    def test_bank_de_is_na(self, fake_src):
        """VCB (bank) must have D/E criterion value=None (skipped)."""
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        watchlist = engine.screen(["VCB"])
        vcb = watchlist[0]
        de_criteria = [c for c in vcb.criteria if c.key == "debt_to_equity"]
        assert de_criteria, "D/E criterion must be present"
        assert de_criteria[0].value is None, "Bank D/E must be N/A"

    def test_scores_in_0_100_range(self, fake_src):
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        watchlist = engine.screen(["FPT", "VCB", "WEAK"])
        for item in watchlist:
            assert 0.0 <= item.score <= 100.0

    def test_missing_ticker_does_not_crash(self, fake_src):
        """Unknown ticker should be gracefully skipped or score 0."""
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        # UNKNOWN not in fake fixture → all data empty → degrades gracefully
        watchlist = engine.screen(["FPT", "UNKNOWN"])
        tickers = [item.ticker for item in watchlist]
        assert "FPT" in tickers

    def test_score_determinism(self, fake_src):
        """Running screen twice with same data must yield identical scores."""
        engine = ScreenerEngine(fake_src, config_path=CONFIG_PATH)
        w1 = engine.screen(["FPT", "VCB", "WEAK"])
        w2 = engine.screen(["FPT", "VCB", "WEAK"])
        for a, b in zip(w1, w2):
            assert a.ticker == b.ticker
            assert a.score == pytest.approx(b.score)

    def test_config_not_found_raises(self, fake_src):
        with pytest.raises(FileNotFoundError):
            ScreenerEngine(fake_src, config_path="/nonexistent/screener.yaml")


# ---------------------------------------------------------------------------
# Regression: _latest_ratio must treat 0.0 as a valid value (not N/A)
# ---------------------------------------------------------------------------

class TestLatestRatioZeroValue:
    """Pin fix: falsy-check was dropping 0.0, causing zero-debt D/E to appear as N/A."""

    def _ratios(self, ticker: str, data: dict) -> Ratios:
        return Ratios(ticker=ticker, period="year", items=data, period_labels=["2024q4"])

    def test_zero_debt_to_equity_is_valid_not_na(self):
        """D/E=0.0 (debt-free company) must return 0.0, not None."""
        r = self._ratios("X", {"debt_to_equity": {"2024q4": 0.0}})
        result = _latest_ratio(r, "debt_to_equity")
        assert result == pytest.approx(0.0), (
            "_latest_ratio dropped 0.0 as if it were missing — falsy-check bug"
        )

    def test_zero_de_passes_filter_as_strong_pass(self):
        """D/E=0.0 must pass the filter (0.0 < any positive threshold)."""
        r = self._ratios("X", {"debt_to_equity": {"2024q4": 0.0}})
        passed, value, _ = filter_debt_to_equity(r, is_bank=False, threshold=1.0)
        assert value == pytest.approx(0.0), "D/E value must be 0.0 not None"
        assert passed is True, "D/E=0.0 should be a strong pass (no debt)"

    def test_none_value_still_na(self):
        """Explicit None in items dict must still resolve to N/A."""
        r = self._ratios("X", {"roe": {"2024q4": None}})
        result = _latest_ratio(r, "roe")
        assert result is None

    def test_nan_value_still_na(self):
        """NaN in items dict must still resolve to N/A."""
        import math
        r = self._ratios("X", {"roe": {"2024q4": float("nan")}})
        result = _latest_ratio(r, "roe")
        assert result is None

    def test_nonzero_value_unaffected(self):
        """Non-zero values must still be returned correctly (regression guard)."""
        r = self._ratios("X", {"roe": {"2024q4": 0.20}})
        result = _latest_ratio(r, "roe")
        assert result == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# Regression: universe-median P/E must exclude the target ticker itself
# ---------------------------------------------------------------------------

class TestSectorMedianPEExcludesTarget:
    """Pin fix: in small universes the fallback median was including the target's
    own P/E, so the stock was partially benchmarked against itself."""

    def _make_ratios(self, ticker: str, pe: float) -> Ratios:
        return Ratios(
            ticker=ticker, period="year",
            items={"pe_ratio": {"2024q4": pe}},
            period_labels=["2024q4"],
        )

    def _make_company(self, ticker: str, sector: str) -> CompanyInfo:
        return CompanyInfo(
            ticker=ticker, organ_name=ticker, sector=sector,
            icb_code="9999", market_cap=100e12, current_price=50_000,
            is_bank=False,
        )

    def test_target_excluded_from_universe_median(self):
        """Universe has 2 tickers: target=AAA (P/E=100), peer=BBB (P/E=10).
        Sector has only 1 peer (<3), so universe-median fallback kicks in.
        Without fix: median([100, 10]) = 55.
        With fix: median([10]) = 10  (AAA excluded).
        """
        all_ratios = {
            "AAA": self._make_ratios("AAA", pe=100.0),
            "BBB": self._make_ratios("BBB", pe=10.0),
        }
        all_companies = {
            "AAA": self._make_company("AAA", sector="SmallSector"),
            "BBB": self._make_company("BBB", sector="OtherSector"),  # different sector → <3 peers
        }
        median_pe = _sector_median_pe(all_ratios, all_companies, ticker="AAA")
        # Only BBB (P/E=10) must be in the median calculation
        assert median_pe == pytest.approx(10.0), (
            f"Expected 10.0 (BBB only) but got {median_pe}. "
            "AAA was included in its own median benchmark."
        )

    def test_sector_path_unchanged_still_excludes_target(self):
        """When sector has >=3 peers the sector-median path already excludes target.
        Verify it still works after refactor."""
        all_ratios = {
            "AAA": self._make_ratios("AAA", pe=50.0),
            "B":   self._make_ratios("B",   pe=10.0),
            "C":   self._make_ratios("C",   pe=12.0),
            "D":   self._make_ratios("D",   pe=14.0),
        }
        all_companies = {
            "AAA": self._make_company("AAA", sector="Tech"),
            "B":   self._make_company("B",   sector="Tech"),
            "C":   self._make_company("C",   sector="Tech"),
            "D":   self._make_company("D",   sector="Tech"),
        }
        median_pe = _sector_median_pe(all_ratios, all_companies, ticker="AAA")
        # Sector peers B/C/D have P/E 10/12/14 → median 12; AAA (50) excluded
        assert median_pe == pytest.approx(12.0), (
            f"Expected sector median 12.0 but got {median_pe}"
        )


# ---------------------------------------------------------------------------
# Live smoke test (gated behind RUN_LIVE_VNSTOCK=1)
# ---------------------------------------------------------------------------

_LIVE = os.environ.get("RUN_LIVE_VNSTOCK", "0") == "1"


@pytest.mark.skipif(not _LIVE, reason="Set RUN_LIVE_VNSTOCK=1 to run live tests")
@pytest.mark.live
class TestScreenerLive:
    def test_screen_vn30_live(self, tmp_path):
        from data.vn import VnstockSource, CachedDataSource
        src = CachedDataSource(
            VnstockSource(throttle_seconds=3.5),
            cache_dir=str(tmp_path / "vn_cache"),
        )
        engine = ScreenerEngine(src, config_path=CONFIG_PATH)
        # Screen a small subset to stay within rate limits
        watchlist = engine.screen(["FPT", "VCB", "HPG"])
        assert len(watchlist) == 3
        assert watchlist[0].rank == 1
        for item in watchlist:
            assert 0.0 <= item.score <= 100.0
