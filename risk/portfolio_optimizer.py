"""Portfolio optimization: Kelly criterion, correlation matrix, allocation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class KellyResult:
    """Kelly criterion optimization result."""

    optimal_fraction: float
    half_kelly: float
    quarter_kelly: float
    expected_growth: float
    risk_of_ruin: float


class KellyOptimizer:
    """Kelly criterion for position sizing."""

    def optimize(self, win_rate: float, avg_win: float, avg_loss: float) -> KellyResult:
        """Calculate Kelly fraction from win rate and payoff.

        Args:
            win_rate: Probability of winning trade
            avg_win: Average win amount (positive)
            avg_loss: Average loss amount (positive)

        Returns:
            KellyResult with optimal and conservative fractions
        """
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return KellyResult(0.0, 0.0, 0.0, 0.0, 1.0)

        # Kelly fraction = (p*b - q) / b
        # where p = win rate, q = loss rate, b = avg_win/avg_loss
        b = avg_win / avg_loss
        kelly = (win_rate * b - (1 - win_rate)) / b
        kelly = max(0.0, min(1.0, kelly))

        # Expected geometric growth
        expected_growth = win_rate * np.log(1 + kelly * b) + (1 - win_rate) * np.log(
            1 - kelly
        )

        # Risk of ruin (simplified)
        risk_of_ruin = (1 - win_rate) ** (1 / kelly) if kelly > 0 else 1.0

        return KellyResult(
            optimal_fraction=kelly,
            half_kelly=kelly * 0.5,
            quarter_kelly=kelly * 0.25,
            expected_growth=expected_growth,
            risk_of_ruin=risk_of_ruin,
        )

    def from_returns(self, returns: pd.Series) -> KellyResult:
        """Calculate Kelly from historical returns."""
        wins = returns[returns > 0]
        losses = returns[returns < 0]

        win_rate = len(wins) / len(returns) if len(returns) > 0 else 0
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 1

        return self.optimize(win_rate, avg_win, avg_loss)


class PortfolioOptimizer:
    """Multi-asset portfolio optimization."""

    def __init__(self, returns_df: pd.DataFrame):
        self.returns = returns_df
        self.n_assets = len(returns_df.columns)

    def correlation_matrix(self) -> pd.DataFrame:
        """Return correlation matrix of returns."""
        return self.returns.corr()

    def covariance_matrix(self) -> pd.DataFrame:
        """Return annualized covariance matrix."""
        return self.returns.cov() * 252

    def minimum_variance_weights(self) -> pd.Series:
        """Compute minimum variance portfolio weights."""
        cov = self.covariance_matrix().values
        n = cov.shape[0]

        # Analytical solution: w = C^-1 * 1 / (1^T * C^-1 * 1)
        ones = np.ones(n)
        try:
            inv_cov = np.linalg.inv(cov)
            weights = inv_cov @ ones / (ones.T @ inv_cov @ ones)
        except np.linalg.LinAlgError:
            logger.warning("Covariance matrix singular, using pseudo-inverse")
            inv_cov = np.linalg.pinv(cov)
            weights = inv_cov @ ones / (ones.T @ inv_cov @ ones)

        return pd.Series(weights, index=self.returns.columns)

    def equal_risk_contribution_weights(self) -> pd.Series:
        """Compute Equal Risk Contribution (ERC) portfolio weights.

        ERC allocates risk equally across assets rather than capital.
        """
        cov = self.covariance_matrix().values
        n = cov.shape[0]

        # Iterative approach
        weights = np.ones(n) / n
        for _ in range(100):
            # Portfolio volatility
            weights.T @ cov @ weights
            # Marginal risk contribution
            mrc = cov @ weights
            # Risk contribution
            rc = weights * mrc
            # Update weights toward equal RC
            weights = weights * (1 / rc) / np.sum(1 / rc)
            weights = weights / weights.sum()

        return pd.Series(weights, index=self.returns.columns)

    def backtest_allocations(self, weights: pd.Series) -> pd.Series:
        """Backtest a set of weights."""
        portfolio_returns = self.returns @ weights
        cumulative = (1 + portfolio_returns).cumprod()
        return cumulative

    def report(self) -> None:
        """Print portfolio analysis report."""
        corr = self.correlation_matrix()
        self.covariance_matrix()

        print("\n" + "=" * 70)
        print("PORTFOLIO OPTIMIZATION REPORT")
        print("=" * 70)

        print("\nCorrelation Matrix:")
        print(corr.round(2).to_string())

        print("\nAnnualized Volatility:")
        vols = self.returns.std() * np.sqrt(252)
        print(vols.round(4).to_string())

        # Min variance
        mv_weights = self.minimum_variance_weights()
        print("\nMinimum Variance Weights:")
        print(mv_weights.round(4).to_string())

        # ERC
        erc_weights = self.equal_risk_contribution_weights()
        print("\nEqual Risk Contribution Weights:")
        print(erc_weights.round(4).to_string())

        # Kelly for each asset
        print("\nKelly Criterion (per asset):")
        kelly = KellyOptimizer()
        for col in self.returns.columns:
            result = kelly.from_returns(self.returns[col])
            print(
                f"  {col}: optimal={result.optimal_fraction:.2%}, half={result.half_kelly:.2%}, "
                f"expected_growth={result.expected_growth:.4f}"
            )

        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test with synthetic multi-asset returns
    np.random.seed(42)
    n_days = 500

    # Correlated returns
    cov = np.array(
        [
            [0.0004, 0.0001, 0.00005],
            [0.0001, 0.0006, 0.00008],
            [0.00005, 0.00008, 0.0003],
        ]
    )
    means = [0.0005, 0.0003, 0.0002]

    returns = np.random.multivariate_normal(means, cov, n_days)
    df = pd.DataFrame(returns, columns=["BTC", "ETH", "SOL"])

    opt = PortfolioOptimizer(df)
    opt.report()
