"""Risk analysis: Monte Carlo simulation and drawdown analysis."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    original_cagr: float
    original_max_dd: float
    mc_mean_cagr: float
    mc_median_cagr: float
    mc_worst_cagr: float
    mc_mean_max_dd: float
    mc_worst_max_dd: float
    prob_positive_return: float
    prob_dd_under_20: float
    equity_paths: np.ndarray


class MonteCarloSimulator:
    """Run Monte Carlo simulation on trading returns."""

    def __init__(self, n_simulations: int = 1000, n_days: int = 252):
        self.n_simulations = n_simulations
        self.n_days = n_days

    def run(self, returns: pd.Series, initial_capital: float = 100000) -> MonteCarloResult:
        """Run Monte Carlo by reshuffling returns with replacement.
        
        Args:
            returns: Daily returns series (can include 0 for non-trading days)
            initial_capital: Starting capital
        
        Returns:
            MonteCarloResult with statistics and equity paths
        """
        returns = returns.dropna().values
        if len(returns) == 0:
            raise ValueError("No returns data")

        # Original stats
        original_cagr = self._cagr(returns)
        original_max_dd = self._max_drawdown(returns)

        # Run simulations
        paths = np.zeros((self.n_simulations, self.n_days))
        cagrs = []
        max_dds = []

        for i in range(self.n_simulations):
            sampled = np.random.choice(returns, size=self.n_days, replace=True)
            equity = initial_capital * np.cumprod(1 + sampled)
            paths[i] = equity
            cagrs.append(self._cagr(sampled))
            max_dds.append(self._max_drawdown(sampled))

        cagrs = np.array(cagrs)
        max_dds = np.array(max_dds)

        result = MonteCarloResult(
            original_cagr=original_cagr,
            original_max_dd=original_max_dd,
            mc_mean_cagr=float(np.mean(cagrs)),
            mc_median_cagr=float(np.median(cagrs)),
            mc_worst_cagr=float(np.percentile(cagrs, 5)),
            mc_mean_max_dd=float(np.mean(max_dds)),
            mc_worst_max_dd=float(np.percentile(max_dds, 95)),
            prob_positive_return=float(np.mean(cagrs > 0)),
            prob_dd_under_20=float(np.mean(max_dds < 0.20)),
            equity_paths=paths,
        )

        self._log_results(result)
        return result

    def _cagr(self, returns: np.ndarray) -> float:
        """Calculate CAGR from daily returns."""
        total_return = np.prod(1 + returns) - 1
        n_years = len(returns) / 252
        if n_years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / n_years) - 1

    def _max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate max drawdown from returns."""
        equity = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        return float(np.min(drawdown))

    def _log_results(self, result: MonteCarloResult):
        logger.info("=" * 60)
        logger.info("MONTE CARLO SIMULATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Original CAGR:      {result.original_cagr:>8.2%}")
        logger.info(f"Original Max DD:    {result.original_max_dd:>8.2%}")
        logger.info(f"MC Mean CAGR:       {result.mc_mean_cagr:>8.2%}")
        logger.info(f"MC Median CAGR:     {result.mc_median_cagr:>8.2%}")
        logger.info(f"MC Worst 5% CAGR:   {result.mc_worst_cagr:>8.2%}")
        logger.info(f"MC Mean Max DD:     {result.mc_mean_max_dd:>8.2%}")
        logger.info(f"MC Worst 5% Max DD: {result.mc_worst_max_dd:>8.2%}")
        logger.info(f"P(CAGR > 0):        {result.prob_positive_return:>8.1%}")
        logger.info(f"P(Max DD < 20%):    {result.prob_dd_under_20:>8.1%}")
        logger.info("=" * 60)


class DrawdownAnalyzer:
    """Analyze drawdown characteristics."""

    def __init__(self, equity_curve: pd.Series):
        self.equity = equity_curve
        self.peak = equity_curve.expanding().max()
        self.drawdown = (equity_curve - self.peak) / self.peak

    def summary(self) -> dict:
        """Return drawdown statistics."""
        dd_series = self.drawdown

        max_dd = dd_series.min()
        max_dd_date = dd_series.idxmin()

        # Find recovery
        peak_before_dd = self.peak.loc[:max_dd_date].iloc[-1]
        recovery = self.equity.loc[max_dd_date:]
        recovered = recovery[recovery >= peak_before_dd]
        recovery_date = recovered.index[0] if not recovered.empty else None

        # Duration
        dd_periods = dd_series < 0
        dd_starts = dd_periods[dd_periods != dd_periods.shift()].cumsum()
        durations = dd_periods.groupby(dd_starts).sum()
        max_duration = durations.max() if not durations.empty else 0

        return {
            "max_drawdown": float(max_dd),
            "max_drawdown_date": max_dd_date,
            "recovery_date": recovery_date,
            "max_duration_days": int(max_duration),
            "avg_drawdown": float(dd_series[dd_series < 0].mean()),
            "dd_frequency": float((dd_series < -0.05).sum() / len(dd_series)),
        }

    def streak_analysis(self) -> pd.DataFrame:
        """Analyze winning/losing streaks."""
        returns = self.equity.pct_change().dropna()
        positive = returns > 0

        streaks = []
        current_streak = 1
        current_type = "win" if positive.iloc[0] else "loss"

        for is_pos in positive.iloc[1:]:
            if (is_pos and current_type == "win") or (not is_pos and current_type == "loss"):
                current_streak += 1
            else:
                streaks.append({"type": current_type, "length": current_streak})
                current_type = "win" if is_pos else "loss"
                current_streak = 1

        streaks.append({"type": current_type, "length": current_streak})
        df = pd.DataFrame(streaks)

        if not df.empty:
            win_streaks = df[df["type"] == "win"]["length"]
            loss_streaks = df[df["type"] == "loss"]["length"]

            logger.info(f"Max win streak:  {win_streaks.max() if not win_streaks.empty else 0} days")
            logger.info(f"Max loss streak: {loss_streaks.max() if not loss_streaks.empty else 0} days")
            logger.info(f"Avg loss streak: {loss_streaks.mean() if not loss_streaks.empty else 0:.1f} days")

        return df


if __name__ == "__main__":
    # Test with synthetic returns
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 500))

    mc = MonteCarloSimulator(n_simulations=500, n_days=252)
    result = mc.run(returns)

    equity = 100000 * (1 + returns).cumprod()
    analyzer = DrawdownAnalyzer(equity)
    print("\nDrawdown Summary:")
    print(analyzer.summary())
    analyzer.streak_analysis()
