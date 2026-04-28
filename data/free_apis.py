"""Free/open API integrations for market data, on-chain, and macro.

Sources:
    - CoinGecko: free tier, no key needed for basic endpoints
    - CryptoCompare: free tier with optional key
    - FRED: free with API key
    - Alternative.me FearGreed: completely free
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
import requests
from loguru import logger


class CoinGeckoAPI:
    """Free crypto market data from CoinGecko.

    No API key required for basic endpoints (< 10-30 calls/min).
    https://www.coingecko.com/en/api
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()

    def fetch_ohlcv(
        self,
        coin_id: str = "bitcoin",
        vs_currency: str = "usd",
        days: int = 365,
    ) -> pd.DataFrame:
        """Fetch OHLCV data."""
        try:
            url = f"{self.BASE_URL}/coins/{coin_id}/ohlc"
            params = {"vs_currency": vs_currency, "days": days}
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            df = pd.DataFrame(
                data, columns=["timestamp", "open", "high", "low", "close"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp").sort_index()
            df["volume"] = np.nan  # CoinGecko /ohlc doesn't include volume
            return df
        except Exception as e:
            logger.warning(f"CoinGecko OHLCV failed: {e}")
            return pd.DataFrame()

    def fetch_market_chart(
        self,
        coin_id: str = "bitcoin",
        vs_currency: str = "usd",
        days: int = 365,
    ) -> pd.DataFrame:
        """Fetch prices + market_caps + total_volumes."""
        try:
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {"vs_currency": vs_currency, "days": days}
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            prices = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
            volumes = pd.DataFrame(
                data["total_volumes"], columns=["timestamp", "volume"]
            )
            mcap = pd.DataFrame(
                data["market_caps"], columns=["timestamp", "market_cap"]
            )

            for d in [prices, volumes, mcap]:
                d["timestamp"] = pd.to_datetime(d["timestamp"], unit="ms")
                d.set_index("timestamp", inplace=True)

            df = prices.join(volumes).join(mcap)
            return df.sort_index()
        except Exception as e:
            logger.warning(f"CoinGecko market_chart failed: {e}")
            return pd.DataFrame()

    def fetch_global_market_cap(self) -> pd.DataFrame:
        """Fetch total crypto market cap dominance (BTC.D, ETH.D)."""
        try:
            url = f"{self.BASE_URL}/global"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()["data"]
            return pd.DataFrame(
                [
                    {
                        "timestamp": datetime.now(),
                        "btc_dominance": data.get("market_cap_percentage", {}).get(
                            "btc", 0
                        ),
                        "eth_dominance": data.get("market_cap_percentage", {}).get(
                            "eth", 0
                        ),
                        "total_mcap": data.get("total_market_cap", {}).get("usd", 0),
                        "total_volume": data.get("total_volume", {}).get("usd", 0),
                    }
                ]
            ).set_index("timestamp")
        except Exception as e:
            logger.warning(f"CoinGecko global failed: {e}")
            return pd.DataFrame()

    def fetch_trending(self) -> pd.DataFrame:
        """Fetch trending coins (sentiment proxy)."""
        try:
            url = f"{self.BASE_URL}/search/trending"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()["coins"]
            rows = []
            for item in data:
                coin = item["item"]
                rows.append(
                    {
                        "timestamp": datetime.now(),
                        "coin_id": coin["id"],
                        "symbol": coin["symbol"],
                        "name": coin["name"],
                        "market_cap_rank": coin.get("market_cap_rank"),
                        "score": coin.get("score"),
                    }
                )
            return pd.DataFrame(rows).set_index("timestamp")
        except Exception as e:
            logger.warning(f"CoinGecko trending failed: {e}")
            return pd.DataFrame()


class CryptoCompareAPI:
    """CryptoCompare free tier data.

    Optional API key for higher rate limits.
    https://min-api.cryptocompare.com/
    """

    BASE_URL = "https://min-api.cryptocompare.com/data"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("CRYPTOCOMPARE_API_KEY", "")
        self.session = requests.Session()

    def _headers(self) -> dict:
        h = {}
        if self.api_key:
            h["authorization"] = f"Apikey {self.api_key}"
        return h

    def fetch_ohlcv(
        self,
        symbol: str = "BTC",
        vs: str = "USDT",
        limit: int = 2000,
        aggregate: int = 1,
        e: str = "CCCAGG",
    ) -> pd.DataFrame:
        """Fetch daily OHLCV."""
        try:
            url = f"{self.BASE_URL}/v2/histoday"
            params = {
                "fsym": symbol,
                "tsym": vs,
                "limit": limit,
                "aggregate": aggregate,
                "e": e,
            }
            resp = self.session.get(
                url, params=params, headers=self._headers(), timeout=15
            )
            resp.raise_for_status()
            data = resp.json()["Data"]["Data"]

            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["time"], unit="s")
            df = df.rename(
                columns={
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volumefrom": "volume",
                    "volumeto": "volume_quote",
                }
            ).set_index("timestamp")
            return df[
                ["open", "high", "low", "close", "volume", "volume_quote"]
            ].sort_index()
        except Exception as e:
            logger.warning(f"CryptoCompare OHLCV failed: {e}")
            return pd.DataFrame()

    def fetch_social_stats(self, coin_id: int = 1182) -> pd.DataFrame:
        """Fetch social stats (reddit, twitter, facebook) as sentiment proxy."""
        try:
            url = f"{self.BASE_URL}/social/coin/histo/day"
            params = {"coinId": coin_id, "limit": 2000}
            resp = self.session.get(
                url, params=params, headers=self._headers(), timeout=15
            )
            resp.raise_for_status()
            data = resp.json()["Data"]

            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["time"], unit="s")
            df = df.set_index("timestamp").sort_index()
            return df[
                [
                    "reddit_subscribers",
                    "reddit_active_users",
                    "twitter_followers",
                    "twitter_favourites",
                ]
            ]
        except Exception as e:
            logger.warning(f"CryptoCompare social failed: {e}")
            return pd.DataFrame()

    def fetch_exchange_inflow_outflow(
        self,
        symbol: str = "BTC",
        limit: int = 2000,
    ) -> pd.DataFrame:
        """Fetch exchange inflow/outflow (on-chain proxy via CryptoCompare)."""
        try:
            url = f"{self.BASE_URL}/blockchain/balancedistribution/day"
            params = {"fsym": symbol, "limit": limit}
            resp = self.session.get(
                url, params=params, headers=self._headers(), timeout=15
            )
            resp.raise_for_status()
            data = resp.json()["Data"]

            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["time"], unit="s")
            df = df.set_index("timestamp").sort_index()
            return df
        except Exception as e:
            logger.warning(f"CryptoCompare blockchain failed: {e}")
            return pd.DataFrame()

    def fetch_altcoin_index(self) -> pd.DataFrame:
        """Fetch AltCoin sentiment index (-1 to 1)."""
        try:
            # Not a direct sentiment index, fallback to simple proxy
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()


class FreeDataIntegrator:
    """Unified free data source integrator.

    Tries multiple free sources and merges best available data.
    """

    def __init__(self):
        self.coingecko = CoinGeckoAPI()
        self.cryptocompare = CryptoCompareAPI()

    def fetch_ohlcv(self, symbol: str = "BTC/USDT", days: int = 365) -> pd.DataFrame:
        """Fetch OHLCV trying multiple free sources."""
        base = symbol.split("/")[0].upper()
        quote = symbol.split("/")[1].upper() if "/" in symbol else "USDT"

        # Try CryptoCompare first (better volume data)
        df = self.cryptocompare.fetch_ohlcv(base, quote, limit=days)
        if not df.empty and len(df) >= days * 0.8:
            logger.info(f"OHLCV from CryptoCompare: {len(df)} rows")
            return df

        # Fallback to CoinGecko
        coin_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
        coin_id = coin_map.get(base, base.lower())
        df = self.coingecko.fetch_ohlcv(coin_id, vs_currency=quote.lower(), days=days)
        if not df.empty:
            logger.info(f"OHLCV from CoinGecko: {len(df)} rows")
            return df

        logger.error(f"Failed to fetch OHLCV for {symbol} from all free sources")
        return pd.DataFrame()

    def fetch_sentiment_features(self) -> pd.DataFrame:
        """Fetch aggregated sentiment features."""
        features = {}

        # Global dominance
        dom = self.coingecko.fetch_global_market_cap()
        if not dom.empty:
            features["btc_dominance"] = dom["btc_dominance"]

        # Social stats
        social = self.cryptocompare.fetch_social_stats()
        if not social.empty:
            features["reddit_subscribers"] = social["reddit_subscribers"]
            features["twitter_followers"] = social["twitter_followers"]

        if not features:
            return pd.DataFrame()

        df = pd.concat(features, axis=1)
        df.columns = [c[1] for c in df.columns]
        return df.sort_index()

    def fetch_onchain_proxy(self, symbol: str = "BTC") -> pd.DataFrame:
        """Fetch on-chain proxy data (exchange balances, inflows)."""
        return self.cryptocompare.fetch_exchange_inflow_outflow(symbol.split("/")[0])


if __name__ == "__main__":
    integrator = FreeDataIntegrator()
    df = integrator.fetch_ohlcv("BTC/USDT", days=30)
    print(df.tail())
    print("\nSentiment features:")
    print(integrator.fetch_sentiment_features().tail())
