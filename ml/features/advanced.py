"""Advanced features: on-chain, sentiment, macro indicators.
    
Note: These are synthetic/placeholder features since we don't have real-time
on-chain/macro data feeds. In production, integrate Glassnode, Alternative.me, FRED APIs.
"""

import numpy as np
import pandas as pd
from loguru import logger


def add_on_chain_features(df: pd.DataFrame, symbol: str = "BTC/USDT") -> pd.DataFrame:
    """Add synthetic on-chain features (placeholders for real data).
    
    In production, fetch from:
        - Glassnode API: active addresses, hash rate, exchange flows
        - CryptoQuant: exchange reserves, funding rates
    """
    if "BTC" not in symbol:
        return df  # Skip for non-BTC

    data = df.copy()
    n = len(data)

    # Synthetic active addresses (correlated with price + noise)
    data["active_addresses"] = (
        data["volume"].rolling(7).mean() * 1000 +
        np.random.normal(0, data["volume"].std() * 500, n)
    )
    data["active_addresses_ma7"] = data["active_addresses"].rolling(7).mean()
    data["active_addresses_change"] = data["active_addresses"].pct_change(7)

    # Synthetic exchange inflow (negative = bullish)
    data["exchange_inflow"] = (
        -data["returns_1d"].shift(1) * 1000 +
        np.random.normal(0, 500, n)
    )
    data["exchange_inflow_ma7"] = data["exchange_inflow"].rolling(7).mean()

    # Synthetic network value ratio proxy
    data["nvt_proxy"] = data["close"] / (data["volume"] + 1e-10)
    data["nvt_ma7"] = data["nvt_proxy"].rolling(7).mean()

    logger.debug("Added on-chain features (synthetic)")
    return data


def add_sentiment_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add synthetic sentiment features.
    
    In production, fetch from:
        - Alternative.me Fear & Greed Index
        - Santiment: social volume, weighted sentiment
        - Twitter/X API: tweet volume, sentiment score
    """
    data = df.copy()
    n = len(data)

    # Synthetic fear/greed index (0-100, mean-reverting around 50)
    np.random.seed(42)
    fear_greed = [50.0]
    for i in range(1, n):
        # Mean-reverting with momentum from returns
        momentum = data["returns_1d"].iloc[i] * 200 if i < len(data) else 0
        noise = np.random.normal(0, 8)
        val = 0.9 * fear_greed[-1] + 0.1 * (50 + momentum) + noise
        val = max(0, min(100, val))
        fear_greed.append(val)
    data["fear_greed_index"] = fear_greed
    data["fear_greed_ema7"] = data["fear_greed_index"].ewm(span=7).mean()
    data["extreme_greed"] = (data["fear_greed_index"] > 75).astype(int)
    data["extreme_fear"] = (data["fear_greed_index"] < 25).astype(int)

    # Synthetic social volume (correlated with volatility)
    data["social_volume"] = (
        data["volatility_5d"] * 10000 +
        np.random.normal(0, 1000, n)
    )
    data["social_volume_ma7"] = data["social_volume"].rolling(7).mean()

    logger.debug("Added sentiment features (synthetic)")
    return data


def add_macro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add synthetic macro features.
    
    In production, fetch from:
        - FRED API: DXY, 10Y Treasury, Fed Funds Rate
        - TradingEconomics: inflation, unemployment
    """
    data = df.copy()
    n = len(data)

    # Synthetic DXY (negatively correlated with BTC, slow-moving)
    np.random.seed(123)
    dxy = [100.0]
    for i in range(1, n):
        trend = -data["returns_1d"].iloc[max(0, i-5):i].mean() * 50 if i > 0 else 0
        noise = np.random.normal(0, 0.3)
        val = 0.98 * dxy[-1] + 0.02 * (100 + trend) + noise
        dxy.append(val)
    data["dxy_index"] = dxy
    data["dxy_change_5d"] = data["dxy_index"].pct_change(5)

    # Synthetic rates (slow drift)
    rates = [4.5]
    for i in range(1, n):
        noise = np.random.normal(0, 0.05)
        val = max(0, rates[-1] + noise)
        rates.append(val)
    data["fed_rate"] = rates
    data["rate_change_30d"] = data["fed_rate"].diff(30)

    # Risk-on/off proxy (based on DXY + rates)
    data["risk_off_proxy"] = (
        (data["dxy_index"] > data["dxy_index"].rolling(20).mean()).astype(int) +
        (data["fed_rate"] > data["fed_rate"].rolling(20).mean()).astype(int)
    )

    logger.debug("Added macro features (synthetic)")
    return data


def compute_advanced_features(df: pd.DataFrame, symbol: str = "BTC/USDT") -> pd.DataFrame:
    """Compute all advanced features."""
    data = add_on_chain_features(df, symbol)
    data = add_sentiment_features(data)
    data = add_macro_features(data)
    # Drop columns that are entirely NaN (can happen with pct_change on short series)
    all_na = data.columns[data.isna().all()]
    if len(all_na) > 0:
        data = data.drop(columns=all_na)
        logger.debug(f"Dropped all-NaN columns: {list(all_na)}")
    return data
