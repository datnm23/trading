"""Metric helpers for screener backtest: CAGR, max-drawdown, Sharpe, hit-rate.

All functions operate on normalised equity Series (start=1.0).
Reused concept from backtest/engine.py, adapted for daily long-only advisory.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List

import pandas as pd


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RebalanceRecord:
    """Snapshot of one rebalance event."""
    as_of: date
    picks: List[str]           # top-N tickers chosen
    scores: Dict[str, float]   # ticker → composite score


@dataclass
class ScreenerBacktestResult:
    """Full backtest output."""
    portfolio_curve: pd.Series       # date → normalised portfolio value (start=1.0)
    benchmark_curve: pd.Series       # date → normalised benchmark value (start=1.0)
    rebalance_records: List[RebalanceRecord]
    total_return: float
    benchmark_return: float
    cagr: float
    max_drawdown: float
    sharpe: float
    hit_rate: float           # fraction of rebalance periods portfolio > benchmark
    alpha: float              # portfolio excess return vs benchmark (simple difference)
    total_fees_paid: float    # cumulative fee drag as fraction of initial capital
    years: float


# ---------------------------------------------------------------------------
# Scalar metrics
# ---------------------------------------------------------------------------

def compute_cagr(equity: pd.Series, trading_days_per_year: int = 252) -> float:
    """Compound annual growth rate from a normalised equity curve."""
    if len(equity) < 2:
        return 0.0
    total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
    years = len(equity) / trading_days_per_year
    if years <= 0:
        return 0.0
    return (1 + total_return) ** (1.0 / years) - 1.0


def compute_max_drawdown(equity: pd.Series) -> float:
    """Maximum drawdown (negative number; 0.0 = no drawdown ever)."""
    if equity.empty:
        return 0.0
    peak = equity.expanding().max()
    dd = (equity - peak) / peak
    return float(dd.min())


def compute_sharpe(
    equity: pd.Series,
    risk_free_annual: float = 0.045,
    trading_days_per_year: int = 252,
) -> float:
    """Annualised Sharpe ratio from daily returns, net of risk-free rate."""
    rets = equity.pct_change().dropna()
    if rets.empty or rets.std() == 0:
        return 0.0
    rf_daily = (1 + risk_free_annual) ** (1.0 / trading_days_per_year) - 1.0
    excess = rets - rf_daily
    return float(excess.mean() / excess.std() * math.sqrt(trading_days_per_year))


def compute_hit_rate(
    port: pd.Series,
    bench: pd.Series,
    rebalance_dates: List[date],
) -> float:
    """Fraction of hold-periods where portfolio return > benchmark return."""
    if len(rebalance_dates) < 2:
        return 0.0
    wins = 0
    total = 0
    for i in range(len(rebalance_dates) - 1):
        t0 = pd.Timestamp(rebalance_dates[i])
        t1 = pd.Timestamp(rebalance_dates[i + 1])
        port_sub = port.loc[t0:t1]
        bench_sub = bench.loc[t0:t1]
        if len(port_sub) < 2 or len(bench_sub) < 2:
            continue
        port_ret = port_sub.iloc[-1] / port_sub.iloc[0] - 1
        bench_ret = bench_sub.iloc[-1] / bench_sub.iloc[0] - 1
        total += 1
        if port_ret > bench_ret:
            wins += 1
    return wins / total if total > 0 else 0.0
