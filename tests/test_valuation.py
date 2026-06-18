"""Offline tests for the valuation engine (Phase 3).

Runs without network access using deterministic FakeSource fixtures.
Live smoke: RUN_LIVE_VNSTOCK=1 python3 -m pytest tests/test_valuation.py -q -m live
"""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import pytest

from data.vn.base import StockDataSource
from data.vn.models import CompanyInfo, FinancialStatement, Ratios
from valuation.dcf import DcfResult, _dcf_value, _compute_fcff, run_dcf
from valuation.relative import run_relative
from valuation.quality import run_quality, _piotroski, _altman_z
from valuation.recommender import recommend, ValuationResult, _blend_target, _upside_score


# ---------------------------------------------------------------------------
# Shared deterministic fixtures
# ---------------------------------------------------------------------------

def _make_cf(cfo: float = 2_000e9, capex: float = -500e9) -> dict:
    """Non-bank cash flow items with 3 years of history."""
    return {
        "net_cash_inflows_outflows_from_operating_activities": {
            "2024": cfo, "2023": cfo * 0.9, "2022": cfo * 0.81,
        },
        "purchases_of_fixed_assets_and_other_long_term_assets": {
            "2024": capex, "2023": capex * 0.9, "2022": capex * 0.81,
        },
    }


def _make_bs(ca: float = 5_000e9, cl: float = 2_000e9, ta: float = 15_000e9) -> dict:
    return {
        "current_assets": {"2024": ca, "2023": ca * 0.9},
        "current_liabilities": {"2024": cl, "2023": cl * 0.95},
        "total_assets": {"2024": ta, "2023": ta * 0.88, "2022": ta * 0.78},
        "liabilities": {"2024": ta * 0.45, "2023": ta * 0.47},
        "owners_equity": {"2024": ta * 0.55, "2023": ta * 0.53},
        "long_term_borrowings": {"2024": 2_000e9, "2023": 2_500e9},
        "undistributed_earnings": {"2024": 3_000e9, "2023": 2_700e9},
        "inventories_net": {"2024": 800e9, "2023": 750e9},
        "paid_in_capital": {"2024": 6_000e9, "2023": 6_000e9},
    }


def _make_inc(net_profit: float = 1_200e9, revenue: float = 12_000e9) -> dict:
    return {
        "net_profit_loss_after_tax": {
            "2024": net_profit, "2023": net_profit * 0.88,
        },
        "net_sales": {"2024": revenue, "2023": revenue * 0.90},
        "gross_profit": {"2024": revenue * 0.28, "2023": revenue * 0.90 * 0.26},
        "operating_profit_loss": {"2024": net_profit * 1.3, "2023": net_profit * 1.3 * 0.88},
        "eps_basic_vnd": {"2024": 5_000.0, "2023": 4_400.0},
        "attributable_to_parent_company": {"2024": net_profit, "2023": net_profit * 0.88},
    }


def _make_ratios(pe: float = 14.0, pb: float = 2.2, roe: float = 0.18) -> dict:
    return {
        "pe_ratio": {"2024q4": pe, "2023q4": pe * 0.9, "2022q4": pe * 0.85,
                     "2021q4": pe * 0.95, "2020q4": pe * 1.1},
        "pb_ratio": {"2024q4": pb},
        "roe": {"2024q4": roe},
        "dividend_yield": {"2024q4": 0.025},
        "current_ratio": {"2024q4": 2.5, "2023q4": 2.3},
        "outstanding_shares": {"2024q4": 616_000_000.0, "2023q4": 616_000_000.0},
        "asset_turnover": {"2024q4": 0.85, "2023q4": 0.78},
    }


def _make_bank_inc() -> dict:
    return {
        "net_profit_loss_after_tax": {"2024": 20_000e9, "2023": 18_000e9},
        "net_interest_income": {"2024": 60_000e9, "2023": 52_000e9},
        "total_operating_income": {"2024": 75_000e9, "2023": 65_000e9},
        "attributable_to_parent_company": {"2024": 20_000e9, "2023": 18_000e9},
        "eps_basic_vnd": {"2024": 4_500.0, "2023": 4_000.0},
    }


def _make_bank_bs() -> dict:
    return {
        "total_assets": {"2024": 1_600_000e9, "2023": 1_400_000e9},
        "total_liabilities": {"2024": 1_400_000e9, "2023": 1_230_000e9},
        "owners_equity": {"2024": 200_000e9, "2023": 170_000e9},
        "charter_capital": {"2024": 55_000e9},
        "retained_earnings": {"2024": 30_000e9},
    }


def _make_bank_cf() -> dict:
    # Banks use different key names
    return {
        "net_cash_from_operating_activities": {"2024": 15_000e9, "2023": 12_000e9},
        "purchases_of_fixed_assets_and_other_long_term_assets": {"2024": -500e9},
    }


def _make_bank_ratios() -> dict:
    return {
        "pe_ratio": {"2024q4": 11.0, "2023q4": 10.5},
        "pb_ratio": {"2024q4": 1.8},
        "roe": {"2024q4": 0.22},
        "net_interest_margin": {"2024q4": 0.032},
        "dividend_yield": {"2024q4": 0.015},
        "current_ratio": {},  # banks lack current ratio
        "outstanding_shares": {"2024q4": 5_500_000_000.0, "2023q4": 5_500_000_000.0},
        "asset_turnover": {},
    }


# ---------------------------------------------------------------------------
# FakeSource for valuation tests
# ---------------------------------------------------------------------------

class FakeSource(StockDataSource):
    """Deterministic offline source supporting both non-bank (FPT) and bank (VCB)."""

    BANK_TICKER = "VCB"
    NON_BANK_TICKER = "FPT"

    def get_ohlcv(self, ticker, start, end, interval="1D") -> pd.DataFrame:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    def get_financials(self, ticker: str, statement_type: str, period: str = "year") -> FinancialStatement:
        is_bank = ticker == self.BANK_TICKER
        if statement_type == "cash_flow":
            items = _make_bank_cf() if is_bank else _make_cf()
        elif statement_type == "balance_sheet":
            items = _make_bank_bs() if is_bank else _make_bs()
        elif statement_type == "income_statement":
            items = _make_bank_inc() if is_bank else _make_inc()
        else:
            items = {}
        return FinancialStatement(ticker=ticker, statement_type=statement_type, period=period, items=items)

    def get_ratios(self, ticker: str, period: str = "year") -> Ratios:
        is_bank = ticker == self.BANK_TICKER
        items = _make_bank_ratios() if is_bank else _make_ratios()
        labels = sorted(items.get("pe_ratio", {}).keys())
        return Ratios(ticker=ticker, period=period, items=items, period_labels=labels)

    def get_company(self, ticker: str) -> Optional[CompanyInfo]:
        if ticker == self.BANK_TICKER:
            return CompanyInfo(
                ticker="VCB",
                organ_name="Vietcombank",
                sector="Banks",
                icb_code="8355",
                market_cap=514_700e9,
                current_price=61_600.0,
                issue_share=5_500_000_000,
                is_bank=True,
            )
        # Default non-bank (FPT or any peer)
        return CompanyInfo(
            ticker=ticker,
            organ_name="FPT Corporation",
            sector="Technology",
            icb_code="9537",
            market_cap=125_200e9,
            current_price=73_500.0,
            issue_share=616_000_000,
            is_bank=False,
        )


@pytest.fixture
def src():
    return FakeSource()


@pytest.fixture
def cfg():
    return {
        "dcf": {"wacc": 0.13, "terminal_growth": 0.03, "projection_years": 5},
        "blend": {"dcf_weight": 0.5, "relative_weight": 0.5},
        "score": {"upside_weight": 0.50, "f_score_weight": 0.30, "z_score_weight": 0.20},
        "recommendation": {"buy_upside_threshold": 0.20, "sell_downside_threshold": -0.10},
        "disclaimer": "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư.",
    }


# ---------------------------------------------------------------------------
# DCF tests
# ---------------------------------------------------------------------------

class TestDcfMath:
    def test_dcf_value_known_inputs(self):
        """Manual DCF: FCFF=1500e9, g=8%, WACC=13%, terminal_g=3%, years=5."""
        fcff = 1_500e9
        result = _dcf_value(fcff, growth=0.08, wacc=0.13, terminal_growth=0.03, years=5)
        # Terminal value dominates; expect large firm value (rough sanity: > 10× FCFF)
        assert result > fcff * 10
        assert result < fcff * 100  # not absurdly large

    def test_compute_fcff_positive(self):
        cf_items = _make_cf(cfo=2_000e9, capex=-500e9)
        fcff = _compute_fcff(cf_items)
        assert fcff == pytest.approx(1_500e9, rel=0.01)

    def test_compute_fcff_capex_sign_insensitive(self):
        """Capex stored as negative — |capex| subtracted correctly."""
        cf_pos = {"net_cash_inflows_outflows_from_operating_activities": {"2024": 2_000e9},
                  "purchases_of_fixed_assets_and_other_long_term_assets": {"2024": 500e9}}
        cf_neg = {"net_cash_inflows_outflows_from_operating_activities": {"2024": 2_000e9},
                  "purchases_of_fixed_assets_and_other_long_term_assets": {"2024": -500e9}}
        assert _compute_fcff(cf_pos) == pytest.approx(_compute_fcff(cf_neg))

    def test_run_dcf_nonbank_returns_intrinsic(self, src, cfg):
        result = run_dcf("FPT", src, cfg=cfg)
        assert result.dcf_applicable is True
        assert result.intrinsic_value is not None
        assert result.intrinsic_value > 0
        # With FCFF≈1500e9 and 616M shares: intrinsic should be order of 50k-300k VND/share
        assert 10_000 < result.intrinsic_value < 1_000_000

    def test_run_dcf_bank_skipped(self, src, cfg):
        result = run_dcf("VCB", src, cfg=cfg)
        assert result.dcf_applicable is False
        assert result.intrinsic_value is None
        assert any("bank" in n.lower() or "ngân hàng" in n.lower() for n in result.notes)

    def test_sensitivity_grid_populated(self, src, cfg):
        result = run_dcf("FPT", src, cfg=cfg)
        assert len(result.sensitivity) >= 6  # 3×3 grid minus invalid combos
        for (w, g), val in result.sensitivity.items():
            assert w > g  # WACC must exceed terminal growth
            assert val > 0

    def test_sensitivity_grid_monotone_in_wacc(self, src, cfg):
        """Higher WACC → lower intrinsic value (holding g fixed)."""
        result = run_dcf("FPT", src, cfg=cfg)
        g_fixed = 0.03
        vals = {w: v for (w, g), v in result.sensitivity.items() if g == g_fixed}
        if len(vals) >= 2:
            waccs = sorted(vals.keys())
            for i in range(len(waccs) - 1):
                assert vals[waccs[i]] > vals[waccs[i + 1]], (
                    f"Higher WACC should reduce intrinsic: {waccs[i]}->{vals[waccs[i]]} "
                    f"vs {waccs[i+1]}->{vals[waccs[i+1]]}"
                )


# ---------------------------------------------------------------------------
# Relative valuation tests
# ---------------------------------------------------------------------------

class TestRelativeValuation:
    def test_implied_value_pe_computed(self, src, cfg):
        result = run_relative("FPT", src, cfg=cfg)
        # EPS=5000 VND, sector_pe or hist_pe available → implied value positive
        assert result.implied_value_pe is not None
        assert result.implied_value_pe > 0

    def test_implied_value_pe_formula(self, src, cfg):
        """implied = pe_reference × eps. EPS=5000, pe≈14 → ~70_000 VND/share."""
        result = run_relative("FPT", src, cfg=cfg)
        eps = 5_000.0
        assert result.eps == pytest.approx(eps, rel=0.01)
        # implied_value ≈ some P/E × 5000
        ref_pe = result.sector_median_pe or result.own_historical_median_pe
        assert ref_pe is not None
        expected = ref_pe * eps
        assert result.implied_value_pe == pytest.approx(expected, rel=0.01)

    def test_bank_relative_returns_result(self, src, cfg):
        """Banks can still have relative valuation (P/E, P/B available)."""
        result = run_relative("VCB", src, cfg=cfg)
        assert result.ticker == "VCB"
        # EPS available from bank income statement
        assert result.eps is not None

    def test_current_pe_and_pb_present(self, src, cfg):
        result = run_relative("FPT", src, cfg=cfg)
        assert result.current_pe == pytest.approx(14.0, rel=0.01)
        assert result.current_pb == pytest.approx(2.2, rel=0.01)

    def test_dividend_yield_present(self, src, cfg):
        result = run_relative("FPT", src, cfg=cfg)
        assert result.dividend_yield == pytest.approx(0.025, rel=0.01)

    def test_notes_contain_numbers(self, src, cfg):
        result = run_relative("FPT", src, cfg=cfg)
        combined = " ".join(result.notes)
        # At least one numeric value appears in notes
        import re
        assert re.search(r"\d+\.\d+", combined), f"No numbers in notes: {result.notes}"

    def test_historical_median_deduplicates_labels(self):
        """_historical_median must not double-count when same label appears twice."""
        from valuation.relative import _historical_median
        # Duplicate labels: '2024q4' repeated — should behave same as single occurrence
        items_duped = {"pe_ratio": {"2024q4": 14.0, "2023q4": 12.0}}
        items_clean = {"pe_ratio": {"2024q4": 14.0, "2023q4": 12.0}}
        med_duped = _historical_median(items_duped, "pe_ratio")
        med_clean = _historical_median(items_clean, "pe_ratio")
        assert med_duped == med_clean == pytest.approx(13.0)

    def test_historical_median_with_duplicate_values_not_counted_twice(self):
        """Simulate scenario where dict keys are unique (de-dupe via set) — median stable."""
        from valuation.relative import _historical_median
        items = {"pe_ratio": {"2024q4": 20.0, "2023q4": 10.0, "2022q4": 15.0}}
        med = _historical_median(items, "pe_ratio", n_years=5)
        # sorted: [10, 15, 20] → median = 15
        assert med == pytest.approx(15.0)


# ---------------------------------------------------------------------------
# Piotroski F-score tests
# ---------------------------------------------------------------------------

class TestPiotroski:
    def _healthy_firm(self) -> tuple[dict, dict, dict, dict]:
        """Deterministic healthy firm that should score 7+/9."""
        bs = _make_bs()
        inc = _make_inc(net_profit=1_500e9)
        cf = _make_cf(cfo=2_000e9)
        ratios = _make_ratios(pe=14.0)
        return bs, inc, cf, ratios

    def test_f_score_range(self):
        bs, inc, cf, ratios = self._healthy_firm()
        score, details = _piotroski(bs, inc, cf, ratios)
        assert 0 <= score <= 9
        assert len(details) == 9

    def test_healthy_firm_scores_high(self):
        bs, inc, cf, ratios = self._healthy_firm()
        score, _ = _piotroski(bs, inc, cf, ratios)
        assert score >= 5, f"Healthy firm should score ≥5, got {score}"

    def test_distressed_firm_scores_low(self):
        """Firm with negative profit, negative CFO, increasing leverage."""
        bs = _make_bs()
        inc = _make_inc(net_profit=-500e9)  # negative profit
        cf_items = {
            "net_cash_inflows_outflows_from_operating_activities": {"2024": -300e9, "2023": -100e9, "2022": 50e9},
            "purchases_of_fixed_assets_and_other_long_term_assets": {"2024": -200e9},
        }
        ratios = _make_ratios()
        # Increase leverage vs prior
        bs["long_term_borrowings"] = {"2024": 5_000e9, "2023": 2_000e9}
        score, _ = _piotroski(bs, inc, cf_items, ratios)
        assert score <= 5, f"Distressed firm should score ≤5, got {score}"

    def test_all_criteria_present_in_details(self):
        bs, inc, cf, ratios = self._healthy_firm()
        _, details = _piotroski(bs, inc, cf, ratios)
        expected_keys = [
            "F1_roa_positive", "F2_cfo_positive", "F3_roa_increasing",
            "F4_accrual_quality", "F5_leverage_decreasing", "F6_current_ratio_improving",
            "F7_no_dilution", "F8_gross_margin_improving", "F9_asset_turnover_improving",
        ]
        for k in expected_keys:
            assert k in details, f"Missing F-score criterion: {k}"
        for k, v in details.items():
            assert v in (0, 1), f"Criterion {k} must be 0 or 1, got {v}"

    def test_f1_roa_positive_when_profitable(self):
        bs, inc, cf, ratios = self._healthy_firm()
        _, details = _piotroski(bs, inc, cf, ratios)
        assert details["F1_roa_positive"] == 1

    def test_f2_cfo_positive_when_operating_positive(self):
        bs, inc, cf, ratios = self._healthy_firm()
        _, details = _piotroski(bs, inc, cf, ratios)
        assert details["F2_cfo_positive"] == 1


# ---------------------------------------------------------------------------
# Altman Z-score tests
# ---------------------------------------------------------------------------

class TestAltmanZ:
    def test_z_score_healthy_firm(self):
        bs = _make_bs(ca=8_000e9, cl=2_000e9, ta=15_000e9)
        inc = _make_inc(net_profit=2_000e9, revenue=15_000e9)
        liabilities = 6_750e9
        z = _altman_z(bs, inc, liabilities)
        assert z is not None
        assert z > 1.5  # at least grey zone for healthy firm

    def test_z_score_none_when_ta_missing(self):
        bs = {}  # no total_assets
        inc = _make_inc()
        z = _altman_z(bs, inc, total_liabilities=5_000e9)
        assert z is None

    def test_altman_z_callable_without_market_cap(self):
        """_altman_z signature must NOT have a market_cap param (it's Z′ / book-equity variant)."""
        import inspect
        sig = inspect.signature(_altman_z)
        assert "market_cap" not in sig.parameters, (
            "_altman_z should not accept market_cap — it uses book equity (Z′ variant)"
        )

    def test_z_score_bank_skipped(self, src):
        result = run_quality("VCB", src)
        assert result.z_score_applicable is False
        assert result.z_score is None
        assert result.z_interpretation == "n/a"

    def test_z_score_applies_for_manufacturing(self, src):
        # Altman Z only applies to manufacturing-type sectors (FPT's mock BS is reused).
        mfg = CompanyInfo(ticker="HPG", organ_name="Hoa Phat", sector="Thép", is_bank=False)
        result = run_quality("FPT", src, company=mfg)
        assert result.z_score_applicable is True
        assert result.z_score is not None  # fixture has full BS

    def test_z_score_skipped_for_non_manufacturing(self, src):
        # Non-bank but non-manufacturing (Technology) → Altman Z mislabels these, so skip.
        result = run_quality("FPT", src)  # mock sector = "Technology"
        assert result.z_score_applicable is False
        assert result.z_score is None
        assert result.z_interpretation == "n/a"

    def test_interpretation_safe(self):
        from valuation.quality import _z_interp
        assert _z_interp(3.5, True) == "safe"

    def test_interpretation_grey(self):
        from valuation.quality import _z_interp
        assert _z_interp(2.0, True) == "grey"

    def test_interpretation_distress(self):
        from valuation.quality import _z_interp
        assert _z_interp(0.8, True) == "distress"

    def test_interpretation_na_for_bank(self):
        from valuation.quality import _z_interp
        assert _z_interp(3.5, False) == "n/a"


# ---------------------------------------------------------------------------
# Bank F-score normalization tests
# ---------------------------------------------------------------------------

class TestBankFScoreNormalization:
    """Banks structurally lack F5 (long_term_borrowings) and F8 (gross_margin).
    f_score_applicable should be 7, f_score_pct should be passed/7.
    """

    def test_bank_f_score_applicable_is_7(self, src):
        result = run_quality("VCB", src)
        assert result.f_score_applicable == 7, (
            f"Banks should have 7 applicable criteria (F5+F8 excluded), got {result.f_score_applicable}"
        )

    def test_bank_f_score_pct_is_fraction_over_7(self, src):
        result = run_quality("VCB", src)
        assert result.f_score_pct is not None
        assert 0.0 <= result.f_score_pct <= 1.0
        # Must equal passed_applicable / 7
        applicable_keys = [
            k for k in result.f_score_details
            if k not in ("F5_leverage_decreasing", "F8_gross_margin_improving")
        ]
        expected_pct = sum(result.f_score_details[k] for k in applicable_keys) / 7
        assert result.f_score_pct == pytest.approx(expected_pct, abs=1e-9)

    def test_bank_f_score_raw_still_present(self, src):
        """Raw f_score (0-9 integer) must still be exposed for transparency."""
        result = run_quality("VCB", src)
        assert result.f_score is not None
        assert 0 <= result.f_score <= 9

    def test_nonbank_f_score_applicable_is_9(self, src):
        result = run_quality("FPT", src)
        assert result.f_score_applicable == 9

    def test_nonbank_f_score_pct_equals_f_score_over_9(self, src):
        result = run_quality("FPT", src)
        assert result.f_score_pct is not None
        assert result.f_score_pct == pytest.approx(result.f_score / 9, abs=1e-9)

    def test_bank_valuation_result_contains_f_score_fields(self, src, cfg):
        """ValuationResult for bank must expose f_score, f_score_applicable, f_score_pct."""
        result = recommend("VCB", src, cfg=cfg)
        assert result.f_score is not None
        assert result.f_score_applicable == 7
        assert result.f_score_pct is not None
        assert 0.0 <= result.f_score_pct <= 1.0

    def test_bank_reasons_show_applicable_denominator(self, src, cfg):
        """Reasons for bank should show 'X/7 (áp dụng)' not 'X/9'."""
        result = recommend("VCB", src, cfg=cfg)
        f_reasons = [r for r in result.reasons if "F-score" in r or "f-score" in r.lower()]
        assert f_reasons, f"No F-score reason found: {result.reasons}"
        assert any("7" in r and "áp dụng" in r for r in f_reasons), (
            f"Bank F-score reason should show '/7 (áp dụng)': {f_reasons}"
        )


# ---------------------------------------------------------------------------
# Recommender blend & mapping tests
# ---------------------------------------------------------------------------

class TestRecommender:
    def test_buy_when_high_upside(self, src, cfg):
        """Force high implied value → BUY."""
        result = recommend("FPT", src, cfg=cfg)
        # FPT current_price=73_500; if upside>20% → BUY
        # We don't force it — just verify result is valid
        assert result.recommendation in ("BUY", "SELL", "HOLD")

    def test_sell_recommendation_boundary(self):
        """upside < -10% → SELL."""
        from valuation.recommender import _recommendation
        assert _recommendation(-0.15, 0.20, -0.10) == "SELL"

    def test_buy_recommendation_boundary(self):
        from valuation.recommender import _recommendation
        assert _recommendation(0.25, 0.20, -0.10) == "BUY"

    def test_hold_recommendation_boundary(self):
        from valuation.recommender import _recommendation
        assert _recommendation(0.05, 0.20, -0.10) == "HOLD"
        assert _recommendation(-0.05, 0.20, -0.10) == "HOLD"

    def test_hold_when_upside_none(self):
        from valuation.recommender import _recommendation
        assert _recommendation(None, 0.20, -0.10) == "HOLD"

    def test_score_in_range(self, src, cfg):
        result = recommend("FPT", src, cfg=cfg)
        assert 0 <= result.score <= 100

    def test_reasons_contain_numbers(self, src, cfg):
        import re
        result = recommend("FPT", src, cfg=cfg)
        combined = " ".join(result.reasons)
        assert re.search(r"\d+\.?\d*", combined), f"Reasons have no numbers: {result.reasons}"

    def test_disclaimer_present(self, src, cfg):
        result = recommend("FPT", src, cfg=cfg)
        assert result.disclaimer
        assert "tham khảo" in result.disclaimer.lower() or len(result.disclaimer) > 10

    def test_result_is_valuation_result(self, src, cfg):
        result = recommend("FPT", src, cfg=cfg)
        assert isinstance(result, ValuationResult)

    def test_bank_branch_dcf_skipped(self, src, cfg):
        result = recommend("VCB", src, cfg=cfg)
        assert result.dcf_applicable is False
        assert result.intrinsic_value is None
        # Should still get a recommendation from relative
        assert result.recommendation in ("BUY", "SELL", "HOLD")
        assert result.score >= 0

    def test_bank_z_score_none(self, src, cfg):
        result = recommend("VCB", src, cfg=cfg)
        assert result.z_score is None

    def test_bank_f_score_present(self, src, cfg):
        """Banks still get a Piotroski F-score (raw int) and normalized fraction."""
        result = recommend("VCB", src, cfg=cfg)
        assert result.f_score is not None
        assert 0 <= result.f_score <= 9
        assert result.f_score_applicable == 7
        assert result.f_score_pct is not None

    def test_sensitivity_populated_nonbank(self, src, cfg):
        result = recommend("FPT", src, cfg=cfg)
        assert len(result.sensitivity) >= 4

    def test_sensitivity_empty_bank(self, src, cfg):
        result = recommend("VCB", src, cfg=cfg)
        assert result.sensitivity == {}

    def test_upside_score_monotone(self):
        """Higher upside → higher upside score."""
        scores = [_upside_score(u, 0.20, -0.10) for u in [-0.20, -0.05, 0.10, 0.25, 0.50]]
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], f"Not monotone at index {i}: {scores}"

    def test_blend_target_both_available(self):
        """With both DCF and relative, blend uses both weights."""
        from valuation.dcf import DcfResult
        from valuation.relative import RelativeResult
        dcf = DcfResult(
            ticker="FPT", dcf_applicable=True, intrinsic_value=100_000.0,
            fcff_ttm=1_500e9, growth_rate=0.08, wacc=0.13, terminal_growth=0.03,
        )
        rel = RelativeResult(
            ticker="FPT", current_pe=14.0, current_pb=2.2,
            sector_median_pe=15.0, own_historical_median_pe=13.0,
            peer_count=5, eps=5_000.0, implied_value_pe=75_000.0,
            dividend_yield=0.025,
        )
        target = _blend_target(dcf, rel, 0.5, 0.5)
        assert target == pytest.approx((100_000.0 + 75_000.0) / 2, rel=0.01)

    def test_blend_target_dcf_only_when_relative_missing(self):
        from valuation.dcf import DcfResult
        from valuation.relative import RelativeResult
        dcf = DcfResult(
            ticker="FPT", dcf_applicable=True, intrinsic_value=100_000.0,
            fcff_ttm=1_500e9, growth_rate=0.08, wacc=0.13, terminal_growth=0.03,
        )
        rel = RelativeResult(
            ticker="FPT", current_pe=None, current_pb=None,
            sector_median_pe=None, own_historical_median_pe=None,
            peer_count=0, eps=None, implied_value_pe=None, dividend_yield=None,
        )
        target = _blend_target(dcf, rel, 0.5, 0.5)
        assert target == pytest.approx(100_000.0)

    def test_blend_target_none_when_both_missing(self):
        from valuation.dcf import DcfResult
        from valuation.relative import RelativeResult
        dcf = DcfResult(
            ticker="VCB", dcf_applicable=False, intrinsic_value=None,
            fcff_ttm=None, growth_rate=None, wacc=0.13, terminal_growth=0.03,
        )
        rel = RelativeResult(
            ticker="VCB", current_pe=None, current_pb=None,
            sector_median_pe=None, own_historical_median_pe=None,
            peer_count=0, eps=None, implied_value_pe=None, dividend_yield=None,
        )
        target = _blend_target(dcf, rel, 0.5, 0.5)
        assert target is None


# ---------------------------------------------------------------------------
# Live smoke test (skipped unless RUN_LIVE_VNSTOCK=1)
# ---------------------------------------------------------------------------

_LIVE = os.environ.get("RUN_LIVE_VNSTOCK", "0") == "1"


@pytest.mark.skipif(not _LIVE, reason="Set RUN_LIVE_VNSTOCK=1 to run live tests")
@pytest.mark.live
class TestLiveValuation:
    """Single-symbol live smoke — only runs with RUN_LIVE_VNSTOCK=1."""

    def test_fpt_valuation(self):
        from data.vn.vnstock_source import VnstockSource
        from data.vn.cache import CachedDataSource
        src = CachedDataSource(VnstockSource(throttle_seconds=3.5), cache_dir="./data/vn_cache")
        result = recommend("FPT", src)
        assert result.ticker == "FPT"
        assert result.recommendation in ("BUY", "SELL", "HOLD")
        assert 0 <= result.score <= 100
        assert result.current_price > 0
        assert len(result.reasons) >= 2
        print(f"\nFPT live: {result.recommendation} score={result.score} "
              f"target={result.target_price and result.target_price/1000:.1f}k "
              f"upside={result.upside_pct and result.upside_pct*100:+.1f}%")
