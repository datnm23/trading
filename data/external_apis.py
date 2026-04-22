"""Live API integrations for on-chain, sentiment, and macro data.

Provides unified interface with fallback to synthetic data when API keys
are not available or rate limits are hit.
"""

import os
from typing import Optional, Dict
from datetime import datetime

import requests
import pandas as pd
import numpy as np
from loguru import logger


class FearGreedAPI:
    """Alternative.me Fear & Greed Index."""

    BASE_URL = "https://api.alternative.me/fng/"

    def fetch(self, limit: int = 100) -> pd.DataFrame:
        """Fetch fear & greed data."""
        try:
            resp = requests.get(f"{self.BASE_URL}?limit={limit}", timeout=15)
            resp.raise_for_status()
            data = resp.json()["data"]

            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
            df["value"] = df["value"].astype(float)
            df = df.set_index("timestamp").sort_index()
            return df[["value", "value_classification"]]
        except Exception as e:
            logger.warning(f"FearGreed API failed: {e}. Using fallback.")
            return self._fallback(limit)

    def _fallback(self, limit: int) -> pd.DataFrame:
        """Generate synthetic fear/greed data."""
        dates = pd.date_range(end=datetime.now(), periods=limit, freq="D")
        values = []
        val = 50.0
        for _ in range(limit):
            val = np.clip(val + np.random.normal(0, 5), 0, 100)
            values.append(val)
        df = pd.DataFrame({"value": values, "value_classification": "neutral"}, index=dates)
        return df


class GlassnodeAPI:
    """Glassnode on-chain metrics (requires API key)."""

    BASE_URL = "https://api.glassnode.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GLASSNODE_API_KEY", "")

    def fetch_metric(self, metric: str, asset: str = "BTC", interval: str = "1d") -> pd.DataFrame:
        """Fetch a specific on-chain metric."""
        if not self.api_key:
            logger.warning("Glassnode API key not set. Using fallback.")
            return self._fallback(metric)

        try:
            url = f"{self.BASE_URL}/metrics/{metric}"
            params = {"a": asset, "i": interval, "api_key": self.api_key}
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            df = pd.DataFrame(data)
            df["t"] = pd.to_datetime(df["t"], unit="s")
            df = df.rename(columns={"v": metric, "t": "timestamp"}).set_index("timestamp")
            return df
        except Exception as e:
            logger.warning(f"Glassnode API failed: {e}. Using fallback.")
            return self._fallback(metric)

    def _fallback(self, metric: str) -> pd.DataFrame:
        """Generate synthetic on-chain data."""
        dates = pd.date_range(end=datetime.now(), periods=365, freq="D")
        if "active" in metric:
            values = np.random.lognormal(12, 0.3, len(dates))
        elif "exchange" in metric:
            values = np.random.lognormal(10, 0.5, len(dates))
        else:
            values = np.random.normal(0, 1, len(dates))
        return pd.DataFrame({metric: values}, index=dates)


class FREDAPI:
    """Federal Reserve Economic Data (requires API key)."""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")

    def fetch_series(self, series_id: str) -> pd.DataFrame:
        """Fetch a FRED series (e.g., DGS10, DEXUSEU, FEDFUNDS)."""
        if not self.api_key:
            logger.warning("FRED API key not set. Using fallback.")
            return self._fallback(series_id)

        try:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 500,
            }
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()["observations"]

            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.rename(columns={"value": series_id}).set_index("date").sort_index()
            return df[[series_id]]
        except Exception as e:
            logger.warning(f"FRED API failed: {e}. Using fallback.")
            return self._fallback(series_id)

    def _fallback(self, series_id: str) -> pd.DataFrame:
        """Generate synthetic macro data."""
        dates = pd.date_range(end=datetime.now(), periods=365, freq="D")
        if "DGS" in series_id or "FED" in series_id:
            values = np.clip(np.cumsum(np.random.normal(0, 0.02, len(dates))) + 4.5, 0, 10)
        elif "DEX" in series_id:
            values = np.cumsum(np.random.normal(0, 0.1, len(dates))) + 100
        else:
            values = np.random.normal(0, 1, len(dates))
        return pd.DataFrame({series_id: values}, index=dates)


class DataIntegrator:
    """Unified data integrator combining all APIs with fallback."""

    def __init__(self):
        self.fear_greed = FearGreedAPI()
        self.glassnode = GlassnodeAPI()
        self.fred = FREDAPI()

    def fetch_all(self) -> Dict[str, pd.DataFrame]:
        """Fetch all available external data."""
        results = {}

        # Sentiment
        results["fear_greed"] = self.fear_greed.fetch(limit=365)

        # On-chain
        results["active_addresses"] = self.glassnode.fetch_metric("addresses/active_count", asset="BTC")
        results["exchange_inflow"] = self.glassnode.fetch_metric("flows/exchange_inflow", asset="BTC")

        # Macro
        results["dxy"] = self.fred.fetch_series("DTWEXBGS")
        results["ten_year"] = self.fred.fetch_series("DGS10")
        results["fed_funds"] = self.fred.fetch_series("FEDFUNDS")

        return results

    def to_features(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """Merge external data with price DataFrame as features."""
        data = price_df.copy()
        external = self.fetch_all()

        for name, df in external.items():
            if not df.empty:
                # Resample to daily and forward fill
                df_daily = df.resample("D").last().ffill()
                # Join on index
                for col in df_daily.columns:
                    if col not in data.columns:
                        data[f"ext_{name}_{col}"] = df_daily[col]

        return data.ffill().bfill()


if __name__ == "__main__":
    integrator = DataIntegrator()
    data = integrator.fetch_all()
    for name, df in data.items():
        print(f"\n{name}: {len(df)} rows")
        print(df.tail(3))
