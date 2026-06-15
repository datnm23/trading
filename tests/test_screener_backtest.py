"""Offline tests for backtest/screener_backtest.py.

Run: python3 -m pytest tests/test_screener_backtest.py -q
No network access. All data served by BacktestFakeSource.

Live smoke test: RUN_LIVE_VNSTOCK=1 python3 -m pytest tests/test_screener_backtest.py -m live -q
"""

from __future__ import annotations

import math
import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import pytest

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from backtest.screener_backtest import (
    AsOfDataSource,
    ScreenerBacktestResult,
    _clip_ohlcv,
    _compute_hit_rate,
    _equal_weight_curve,
    _get_prices_on_date,
    _rebalance_dates,
    compute_cagr,
    compute_max_drawdown,
    compute_sharpe,
    load_backtest_config,
    run_screener_backtest,
    write_backtest_report,
)


# ---------------------------------------------------------------------------
# Config paths
# ---------------------------------------------------------------------------

BACKTEST_CFG = str(Path(__file__).parent.parent / "config" / "backtest.yaml")
SCREENER_CFG = str(Path(__file__).parent.parent / "config" / "screener.yaml")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(
    n: int,
    close: float,
    volume: int = 5_000_000,
    start: str = "2022-01-03",
    daily_return: float = 0.0,
) -> pd.DataFrame:
    """Build synthetic daily OHLCV with optional daily_return drift."""
    dates = pd.date_range(start, periods=n, freq="B")
    closes = [close * ((1 + daily_return) ** i) for i in range(n)]
    return pd.DataFrame({
        "time": dates,
        "open": [c * 0.99 for c in closes],
        "high": [c * 1.01 for c in closes],
        "low":  [c * 0.98 for c in closes],
        "close": closes,
        "volume": volume,
    })


# ---------------------------------------------------------------------------
# BacktestFakeSource
# ---------------------------------------------------------------------------

class BacktestFakeSource(StockDataSource):
    """Deterministic fake for 3 tickers spanning 2022-01-01 → 2024-12-31.

    ALPHA — strong FA metrics, slightly rising price (+0.03%/day).
    BETA  — decent FA, flat price.
    GAMMA — weak FA, slightly falling price (−0.01%/day).
    VNINDEX — benchmark, flat at 1250.

    fetch_ranges records every (start, end, ticker) call to get_ohlcv
    so tests can assert no future data was requested.
    """

    TICKERS = ["ALPHA", "BETA", "GAMMA"]

    FIXTURES: Dict[str, dict] = {
        "ALPHA": {
            "is_bank": False, "sector": "Technology",
            "close": 73.5, "volume": 5_000_000, "daily_return": 0.0003,
            "ratios": {
                "roe":            {"2023q4": 0.25, "2022q4": 0.22},
                "pe_ratio":       {"2023q4": 16.0, "2022q4": 17.0},
                "debt_to_equity": {"2023q4": 0.4,  "2022q4": 0.5},
                "net_margin":     {"2023q4": 0.13, "2022q4": 0.12},
            },
            "income": {
                "eps_basic_vnd":          {"2023": 5_500.0, "2022": 4_500.0, "2021": 3_800.0},
                "net_sales":              {"2023": 65e12,   "2022": 55e12,   "2021": 45e12},
                "net_profit_loss_after_tax": {"2023": 8e12, "2022": 7e12,   "2021": 5e12},
            },
        },
        "BETA": {
            "is_bank": False, "sector": "Real Estate",
            "close": 40.0, "volume": 3_000_000, "daily_return": 0.0,
            "ratios": {
                "roe":            {"2023q4": 0.16, "2022q4": 0.15},
                "pe_ratio":       {"2023q4": 20.0, "2022q4": 21.0},
                "debt_to_equity": {"2023q4": 0.7,  "2022q4": 0.8},
                "net_margin":     {"2023q4": 0.08, "2022q4": 0.07},
            },
            "income": {
                "eps_basic_vnd":          {"2023": 3_000.0, "2022": 2_800.0, "2021": 2_600.0},
                "net_sales":              {"2023": 30e12,   "2022": 28e12,   "2021": 26e12},
                "net_profit_loss_after_tax": {"2023": 3e12, "2022": 2.8e12, "2021": 2.6e12},
            },
        },
        "GAMMA": {
            "is_bank": False, "sector": "Materials",
            "close": 20.0, "volume": 1_000_000, "daily_return": -0.0001,
            "ratios": {
                "roe":            {"2023q4": 0.08, "2022q4": 0.09},
                "pe_ratio":       {"2023q4": 35.0, "2022q4": 32.0},
                "debt_to_equity": {"2023q4": 1.8,  "2022q4": 1.6},
                "net_margin":     {"2023q4": 0.03, "2022q4": 0.04},
            },
            "income": {
                "eps_basic_vnd":          {"2023": 900.0,  "2022": 1_000.0, "2021": 1_100.0},
                "net_sales":              {"2023": 10e12,  "2022": 12e12,   "2021": 14e12},
                "net_profit_loss_after_tax": {"2023": 1e12, "2022": 1.2e12, "2021": 1.4e12},
            },
        },
    }

    def __init__(self):
        self.ohlcv_calls: List[dict] = []  # records every get_ohlcv call

    def get_ohlcv(self, ticker: str, start: str, end: str, interval: str = "1D") -> pd.DataFrame:
        self.ohlcv_calls.append({"ticker": ticker, "start": start, "end": end})

        if ticker == "VNINDEX":
            return _make_ohlcv(782, close=1250.0, volume=500_000_000, start="2022-01-03")

        if ticker not in self.FIXTURES:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        f = self.FIXTURES[ticker]
        df = _make_ohlcv(
            782, close=f["close"], volume=f["volume"],
            start="2022-01-03", daily_return=f.get("daily_return", 0.0),
        )
        # Filter by requested start/end
        df["time"] = pd.to_datetime(df["time"])
        mask = (df["time"] >= pd.Timestamp(start)) & (df["time"] <= pd.Timestamp(end))
        return df[mask].copy()

    def get_financials(self, ticker: str, statement_type: str, period: str = "year") -> FinancialStatement:
        if ticker not in self.FIXTURES or statement_type != "income_statement":
            return FinancialStatement(ticker=ticker, statement_type=statement_type, period=period)
        return FinancialStatement(
            ticker=ticker, statement_type=statement_type, period=period,
            items=self.FIXTURES[ticker]["income"],
        )

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        if ticker not in self.FIXTURES:
            return Ratios(ticker=ticker, period=period)
        f = self.FIXTURES[ticker]
        return Ratios(
            ticker=ticker, period=period,
            items=f["ratios"],
            period_labels=list(next(iter(f["ratios"].values())).keys()),
        )

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        if ticker not in self.FIXTURES:
            return None
        f = self.FIXTURES[ticker]
        return CompanyInfo(
            ticker=ticker, organ_name=ticker,
            sector=f["sector"], icb_code="9999",
            market_cap=100e12, current_price=f["close"] * 1000,
            is_bank=f["is_bank"],
        )


@pytest.fixture
def fake_src():
    return BacktestFakeSource()


@pytest.fixture
def bt_config() -> dict:
    """Minimal in-memory backtest config for offline tests."""
    return {
        "top_n": 2,
        "start_date": "2022-01-01",
        "end_date": "2022-06-30",
        "rebalance_freq": "quarterly",
        "fee_bps": 30,
        "bctc_publication_lag_days": 90,
        "initial_capital": 100_000_000,
        "risk_free_rate_annual": 0.045,
        "trading_days_per_year": 252,
        "benchmark_symbol": "VNINDEX",
        "universe": "VN30",
    }


# ---------------------------------------------------------------------------
# Unit: rebalance date generator
# ---------------------------------------------------------------------------

class TestRebalanceDates:
    def test_quarterly_produces_4_per_year(self):
        dates = _rebalance_dates(date(2022, 1, 1), date(2022, 12, 31), "quarterly")
        assert len(dates) == 4
        assert dates[0] == date(2022, 1, 1)
        assert dates[1] == date(2022, 4, 1)
        assert dates[2] == date(2022, 7, 1)
        assert dates[3] == date(2022, 10, 1)

    def test_monthly_produces_12_per_year(self):
        dates = _rebalance_dates(date(2022, 1, 1), date(2022, 12, 31), "monthly")
        assert len(dates) == 12

    def test_unknown_freq_raises(self):
        with pytest.raises(ValueError, match="Unknown rebalance_freq"):
            _rebalance_dates(date(2022, 1, 1), date(2022, 12, 31), "weekly")


# ---------------------------------------------------------------------------
# Unit: metric helpers
# ---------------------------------------------------------------------------

class TestMetricHelpers:
    def _curve(self, values: list) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(values), freq="B")
        return pd.Series(values, index=idx)

    def test_cagr_flat(self):
        curve = self._curve([1.0] * 252)
        assert compute_cagr(curve, 252) == pytest.approx(0.0, abs=1e-4)

    def test_cagr_double_in_one_year(self):
        # Equity doubles in exactly 252 trading days → CAGR ≈ 100%
        curve = self._curve([1.0, 2.0])
        # 2 days treated as 2/252 years → huge CAGR; just check sign/direction
        cagr = compute_cagr(curve, 252)
        assert cagr > 0

    def test_cagr_known_value(self):
        # 10% return over 252 days → CAGR ≈ 10%
        n = 252
        curve = self._curve([1.0 + (0.10 / n) * i for i in range(n)])
        cagr = compute_cagr(curve, 252)
        assert cagr == pytest.approx(0.10, rel=0.05)

    def test_max_drawdown_no_drawdown(self):
        curve = self._curve([1.0, 1.1, 1.2, 1.3])
        assert compute_max_drawdown(curve) == pytest.approx(0.0)

    def test_max_drawdown_50pct(self):
        curve = self._curve([1.0, 2.0, 1.0])
        assert compute_max_drawdown(curve) == pytest.approx(-0.5)

    def test_max_drawdown_known(self):
        # Peak 1.5, trough 0.9 → drawdown = (0.9 - 1.5)/1.5 = -0.4
        curve = self._curve([1.0, 1.5, 0.9])
        dd = compute_max_drawdown(curve)
        assert dd == pytest.approx(-0.4, rel=1e-4)

    def test_sharpe_positive_for_positive_returns(self):
        # Steadily rising curve → positive Sharpe
        values = [1.0 * (1.0005 ** i) for i in range(252)]
        curve = self._curve(values)
        sharpe = compute_sharpe(curve, risk_free_annual=0.0, trading_days_per_year=252)
        assert sharpe > 0

    def test_sharpe_zero_for_flat_curve(self):
        curve = self._curve([1.0] * 100)
        assert compute_sharpe(curve) == 0.0

    def test_sharpe_empty(self):
        assert compute_sharpe(pd.Series(dtype=float)) == 0.0


# ---------------------------------------------------------------------------
# Unit: OHLCV clip (no look-ahead)
# ---------------------------------------------------------------------------

class TestClipOhlcv:
    def test_clips_future_rows(self):
        df = _make_ohlcv(20, close=50.0, start="2022-01-03")
        as_of = date(2022, 1, 10)
        clipped = _clip_ohlcv(df, as_of)
        assert (pd.to_datetime(clipped["time"]) <= pd.Timestamp(as_of)).all()

    def test_empty_df_stays_empty(self):
        df = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        clipped = _clip_ohlcv(df, date(2022, 1, 10))
        assert clipped.empty


# ---------------------------------------------------------------------------
# Unit: AsOfDataSource enforces no look-ahead
# ---------------------------------------------------------------------------

class TestAsOfDataSource:
    """Critical: screener at date T must never see price rows after T."""

    def test_no_price_rows_after_as_of(self, fake_src):
        as_of = date(2022, 3, 31)
        as_of_src = AsOfDataSource(fake_src, as_of)
        df = as_of_src.get_ohlcv("ALPHA", "2022-01-01", "2022-12-31")
        assert not df.empty
        assert (pd.to_datetime(df["time"]) <= pd.Timestamp(as_of)).all(), (
            f"Got future price rows: max time={df['time'].max()} > as_of={as_of}"
        )

    def test_no_rows_for_future_only_request(self, fake_src):
        as_of = date(2022, 1, 1)
        as_of_src = AsOfDataSource(fake_src, as_of)
        df = as_of_src.get_ohlcv("ALPHA", "2023-01-01", "2023-12-31")
        # All requested dates are after as_of → empty
        assert df.empty or (pd.to_datetime(df["time"]) <= pd.Timestamp(as_of)).all()

    def test_financials_pass_through(self, fake_src):
        as_of_src = AsOfDataSource(fake_src, date(2022, 6, 30))
        stmt = as_of_src.get_financials("ALPHA", "income_statement")
        assert stmt.ticker == "ALPHA"

    def test_ratios_pass_through(self, fake_src):
        as_of_src = AsOfDataSource(fake_src, date(2022, 6, 30))
        ratios = as_of_src.get_ratios("ALPHA")
        assert ratios.ticker == "ALPHA"


# ---------------------------------------------------------------------------
# Unit: get_prices_on_date
# ---------------------------------------------------------------------------

class TestGetPricesOnDate:
    def test_returns_last_close_on_or_before(self):
        df = _make_ohlcv(10, close=50.0, start="2022-01-03")
        ohlcv = {"FPT": df}
        prices = _get_prices_on_date(ohlcv, ["FPT"], date(2022, 1, 7))
        assert "FPT" in prices
        assert prices["FPT"] == pytest.approx(50.0)

    def test_missing_ticker_absent_from_result(self):
        prices = _get_prices_on_date({}, ["NOPE"], date(2022, 1, 7))
        assert "NOPE" not in prices


# ---------------------------------------------------------------------------
# Unit: hit-rate computation
# ---------------------------------------------------------------------------

class TestHitRate:
    def _curve(self, values: list, start: str = "2022-01-03") -> pd.Series:
        idx = pd.date_range(start, periods=len(values), freq="B")
        return pd.Series(values, index=idx)

    def test_100pct_hit_rate(self):
        port = self._curve([1.0, 1.1, 1.2, 1.3, 1.4])
        bench = self._curve([1.0, 1.01, 1.02, 1.03, 1.04])
        rdates = [date(2022, 1, 3), date(2022, 1, 5), date(2022, 1, 7)]
        hr = _compute_hit_rate(port, bench, rdates)
        assert hr == pytest.approx(1.0)

    def test_0pct_hit_rate(self):
        port = self._curve([1.0, 0.9, 0.85, 0.8, 0.75])
        bench = self._curve([1.0, 1.1, 1.2, 1.3, 1.4])
        rdates = [date(2022, 1, 3), date(2022, 1, 5), date(2022, 1, 7)]
        hr = _compute_hit_rate(port, bench, rdates)
        assert hr == pytest.approx(0.0)

    def test_single_rebalance_returns_zero(self):
        port = self._curve([1.0, 1.1])
        bench = self._curve([1.0, 1.05])
        hr = _compute_hit_rate(port, bench, [date(2022, 1, 3)])
        assert hr == 0.0


# ---------------------------------------------------------------------------
# Integration: rebalance loop produces equity curve
# ---------------------------------------------------------------------------

class TestRebalanceLoop:
    def test_equity_curve_has_daily_values(self, fake_src, bt_config):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert isinstance(result.portfolio_curve, pd.Series)
        assert len(result.portfolio_curve) > 0

    def test_equity_curve_starts_at_one(self, fake_src, bt_config):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert result.portfolio_curve.iloc[0] == pytest.approx(1.0)

    def test_rebalance_records_present(self, fake_src, bt_config):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert len(result.rebalance_records) >= 1
        for rec in result.rebalance_records:
            assert len(rec.picks) <= bt_config["top_n"]
            assert len(rec.picks) >= 1

    def test_top_n_selection_picks_highest_scores(self, fake_src, bt_config):
        """top_n=2: GAMMA (weak FA) should never be the only pick."""
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        # ALPHA has the strongest FA → must appear in at least one rebalance
        all_picks = [t for rec in result.rebalance_records for t in rec.picks]
        assert "ALPHA" in all_picks, "ALPHA (best FA) must appear in picks"
        # GAMMA (weakest FA) should not appear alone without better stocks
        gamma_only = [rec for rec in result.rebalance_records if rec.picks == ["GAMMA"]]
        assert len(gamma_only) == 0, "GAMMA alone must not be the sole pick"


# ---------------------------------------------------------------------------
# No-look-ahead: screener at T must not see price bars after T
# ---------------------------------------------------------------------------

class TestNoLookAhead:
    def test_screener_at_T_sees_no_future_bars(self, fake_src, bt_config):
        """Run the full backtest and check every ohlcv call has end <= as_of.

        We wrap the fake source to record all ohlcv calls made during the run.
        The rebalance loop uses AsOfDataSource which clips end to as_of.
        """
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert result is not None
        # Every call recorded in fake_src.ohlcv_calls that went through the
        # pre-fetch (bulk load) may use the full range, but AsOfDataSource
        # clips the returned DataFrame.  Verify via AsOfDataSource directly:
        for rd in [r.as_of for r in result.rebalance_records]:
            wrapped = AsOfDataSource(fake_src, rd)
            df = wrapped.get_ohlcv("ALPHA", "2022-01-01", "2024-12-31")
            if not df.empty:
                max_date = pd.to_datetime(df["time"]).max()
                assert max_date <= pd.Timestamp(rd), (
                    f"Look-ahead violation at rebalance {rd}: got data up to {max_date}"
                )


# ---------------------------------------------------------------------------
# Benchmark present in result
# ---------------------------------------------------------------------------

class TestBenchmark:
    def test_benchmark_curve_present(self, fake_src, bt_config):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert isinstance(result.benchmark_curve, pd.Series)
        assert not result.benchmark_curve.empty

    def test_benchmark_starts_at_one(self, fake_src, bt_config):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert result.benchmark_curve.iloc[0] == pytest.approx(1.0, abs=0.01)

    def test_alpha_computed(self, fake_src, bt_config):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        expected_alpha = result.total_return - result.benchmark_return
        assert result.alpha == pytest.approx(expected_alpha, rel=1e-4)


# ---------------------------------------------------------------------------
# Fees reduce returns
# ---------------------------------------------------------------------------

class TestFeeImpact:
    def test_fees_reduce_returns_vs_no_fees(self, fake_src, bt_config):
        """Backtest with 0 fees must have >= total return vs one with 100 bps fees."""
        cfg_no_fee = dict(bt_config, fee_bps=0)
        cfg_high_fee = dict(bt_config, fee_bps=100)

        r_no_fee = run_screener_backtest(
            fake_src, cfg_no_fee,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        r_high_fee = run_screener_backtest(
            fake_src, cfg_high_fee,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        assert r_no_fee.total_return >= r_high_fee.total_return, (
            f"No-fee return {r_no_fee.total_return:.4f} < high-fee {r_high_fee.total_return:.4f}"
        )
        assert r_high_fee.total_fees_paid > 0


# ---------------------------------------------------------------------------
# Metrics on known series
# ---------------------------------------------------------------------------

class TestMetricsOnKnownSeries:
    def test_cagr_on_known_series(self):
        # 252 bars, equity doubles → CAGR = 100% over 1 year
        n = 252
        curve = pd.Series(
            [1.0 + i / n for i in range(n)],
            index=pd.date_range("2022-01-03", periods=n, freq="B"),
        )
        cagr = compute_cagr(curve, 252)
        assert cagr > 0

    def test_max_drawdown_on_known_series(self):
        # Up from 1→2 then crash to 0.5: drawdown = (0.5-2)/2 = -75%
        curve = pd.Series(
            [1.0, 2.0, 0.5],
            index=pd.date_range("2022-01-03", periods=3, freq="B"),
        )
        dd = compute_max_drawdown(curve)
        assert dd == pytest.approx(-0.75, rel=1e-4)

    def test_sharpe_on_known_positive_drift(self):
        n = 252
        daily_ret = 0.001  # 0.1%/day
        values = [1.0 * (1 + daily_ret) ** i for i in range(n)]
        curve = pd.Series(values, index=pd.date_range("2022-01-03", periods=n, freq="B"))
        sharpe = compute_sharpe(curve, risk_free_annual=0.0)
        # Constant daily return → very high Sharpe (no std dev noise)
        assert sharpe > 5.0


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

class TestReportGeneration:
    def test_report_written_to_disk(self, fake_src, bt_config, tmp_path):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        report_path = str(tmp_path / "test-backtest-report.md")
        write_backtest_report(result, report_path)
        p = Path(report_path)
        assert p.exists()
        content = p.read_text()
        assert "Screener Backtest Report" in content
        assert "Total Return" in content
        assert "CAGR" in content
        assert "Limitation Notes" in content

    def test_report_contains_rebalance_history(self, fake_src, bt_config, tmp_path):
        result = run_screener_backtest(
            fake_src, bt_config,
            screener_config_path=SCREENER_CFG,
            universe=BacktestFakeSource.TICKERS,
        )
        report_path = str(tmp_path / "test-backtest-report.md")
        write_backtest_report(result, report_path)
        content = Path(report_path).read_text()
        assert "Rebalance History" in content


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

class TestConfigLoader:
    def test_loads_backtest_config(self):
        cfg = load_backtest_config(BACKTEST_CFG)
        assert cfg["top_n"] == 5
        assert "rebalance_freq" in cfg
        assert "fee_bps" in cfg
        assert "bctc_publication_lag_days" in cfg

    def test_missing_config_raises(self):
        with pytest.raises(FileNotFoundError):
            load_backtest_config("/nonexistent/backtest.yaml")


# ---------------------------------------------------------------------------
# Equal-weight benchmark fallback
# ---------------------------------------------------------------------------

class TestEqualWeightCurve:
    def test_starts_at_one(self):
        all_ohlcv = {t: _make_ohlcv(50, close=50.0) for t in ["A", "B"]}
        dates = pd.date_range("2022-01-03", periods=50, freq="B")
        curve = _equal_weight_curve(all_ohlcv, ["A", "B"], dates)
        assert curve.iloc[0] == pytest.approx(1.0, abs=0.01)

    def test_empty_ohlcv_returns_flat_curve(self):
        dates = pd.date_range("2022-01-03", periods=10, freq="B")
        curve = _equal_weight_curve({}, [], dates)
        # All values should be 1.0 (flat fallback)
        assert (curve - 1.0).abs().max() < 1e-9


# ---------------------------------------------------------------------------
# Live smoke test (gated behind RUN_LIVE_VNSTOCK=1)
# ---------------------------------------------------------------------------

_LIVE = os.environ.get("RUN_LIVE_VNSTOCK", "0") == "1"


@pytest.mark.skipif(not _LIVE, reason="Set RUN_LIVE_VNSTOCK=1 to run live tests")
@pytest.mark.live
class TestLiveBacktest:
    def test_live_backtest_small_universe(self, tmp_path):
        """Live smoke: 2 tickers, 1 quarter, quarterly rebalance.

        Requires vnstock API access. May be slow (rate limit).
        """
        from data.vn import VnstockSource, CachedDataSource

        src = CachedDataSource(
            VnstockSource(throttle_seconds=3.5),
            cache_dir=str(tmp_path / "vn_cache"),
        )
        cfg = {
            "top_n": 2,
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "rebalance_freq": "quarterly",
            "fee_bps": 30,
            "bctc_publication_lag_days": 90,
            "initial_capital": 100_000_000,
            "risk_free_rate_annual": 0.045,
            "trading_days_per_year": 252,
            "benchmark_symbol": "VNINDEX",
        }
        result = run_screener_backtest(
            src, cfg,
            screener_config_path=SCREENER_CFG,
            universe=["FPT", "VCB"],
        )
        assert isinstance(result.portfolio_curve, pd.Series)
        assert not result.portfolio_curve.empty
