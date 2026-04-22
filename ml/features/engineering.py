"""Feature engineering pipeline for ML models."""

import pandas as pd
import numpy as np


def compute_features(df: pd.DataFrame, advanced: bool = False, symbol: str = "BTC/USDT") -> pd.DataFrame:
    """Compute technical and statistical features from OHLCV data.
    
    Args:
        df: OHLCV DataFrame
        advanced: If True, add on-chain, sentiment, macro features
        symbol: For advanced feature context
    
    Returns DataFrame with original columns + engineered features.
    """
    data = df.copy()
    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data["volume"]

    # --- Price-based features ---
    # Returns
    data["returns_1d"] = close.pct_change()
    data["returns_5d"] = close.pct_change(5)
    data["returns_10d"] = close.pct_change(10)
    data["returns_20d"] = close.pct_change(20)
    data["returns_50d"] = close.pct_change(50)
    data["returns_100d"] = close.pct_change(100)

    # Log returns
    data["log_returns"] = np.log(close / close.shift(1))

    # Volatility (rolling std of returns)
    data["volatility_5d"] = data["returns_1d"].rolling(5).std()
    data["volatility_10d"] = data["returns_1d"].rolling(10).std()
    data["volatility_20d"] = data["returns_1d"].rolling(20).std()
    data["volatility_50d"] = data["returns_1d"].rolling(50).std()
    data["volatility_100d"] = data["returns_1d"].rolling(100).std()

    # --- Moving averages and distances ---
    for period in [5, 10, 20, 50, 100, 200]:
        data[f"ema_{period}"] = close.ewm(span=period).mean()
        data[f"sma_{period}"] = close.rolling(period).mean()
        data[f"close_to_ema_{period}"] = close / data[f"ema_{period}"] - 1
        data[f"close_to_sma_{period}"] = close / data[f"sma_{period}"] - 1

    # --- EMA slopes (trend strength / direction) ---
    data["ema_slope_20"] = (data["ema_20"] - data["ema_20"].shift(20)) / data["ema_20"].shift(20)
    data["ema_slope_50"] = (data["ema_50"] - data["ema_50"].shift(20)) / data["ema_50"].shift(20)

    # --- RSI ---
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    data["rsi_14"] = 100 - (100 / (1 + rs))

    # --- MACD ---
    ema_12 = close.ewm(span=12).mean()
    ema_26 = close.ewm(span=26).mean()
    data["macd"] = ema_12 - ema_26
    data["macd_signal"] = data["macd"].ewm(span=9).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]

    # --- ATR ---
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data["atr_14"] = tr.ewm(span=14, adjust=False).mean()
    data["atr_ratio"] = data["atr_14"] / close

    # --- Bollinger Bands ---
    sma_20 = close.rolling(20).mean()
    std_20 = close.rolling(20).std()
    data["bb_upper"] = sma_20 + 2 * std_20
    data["bb_lower"] = sma_20 - 2 * std_20
    data["bb_position"] = (close - data["bb_lower"]) / (data["bb_upper"] - data["bb_lower"] + 1e-10)

    # --- Volume features ---
    data["volume_sma_10"] = volume.rolling(10).mean()
    data["volume_ratio"] = volume / (data["volume_sma_10"] + 1e-10)
    data["volume_change"] = volume.pct_change()

    # OBV
    obv = [0]
    for i in range(1, len(data)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    data["obv"] = obv
    data["obv_ema"] = data["obv"].ewm(span=20).mean()

    # --- Price action features ---
    data["body_size"] = (close - data["open"]).abs() / (high - low + 1e-10)
    data["upper_shadow"] = (high - close.where(close > data["open"], data["open"])) / (high - low + 1e-10)
    data["lower_shadow"] = (close.where(close > data["open"], data["open"]) - low) / (high - low + 1e-10)

    # --- Lag features ---
    for lag in [1, 2, 3, 5]:
        data[f"close_lag_{lag}"] = close.shift(lag)
        data[f"returns_lag_{lag}"] = data["returns_1d"].shift(lag)

    # --- Target: future return direction ---
    data["target_return_5d"] = close.shift(-5) / close - 1
    data["target_direction"] = (data["target_return_5d"] > 0).astype(int)

    # --- Advanced features ---
    if advanced:
        from ml.features.advanced import compute_advanced_features
        data = compute_advanced_features(data, symbol=symbol)

    return data


def prepare_train_data(df: pd.DataFrame, dropna: bool = True) -> tuple:
    """Prepare X, y for training from feature-engineered DataFrame.
    
    Returns (X, y, feature_names)
    """
    feature_cols = [c for c in df.columns if c not in [
        "open", "high", "low", "close", "volume",
        "target_return_5d", "target_direction"
    ]]

    data = df[feature_cols + ["target_direction"]].copy()
    if dropna:
        data = data.dropna()

    X = data[feature_cols].values
    y = data["target_direction"].values
    return X, y, feature_cols
