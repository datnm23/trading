"""Market data module — fetches OHLCV from free sources."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from data.free_apis import CoinGeckoAPI


SYMBOL_MAP = {
    "BTC/USDT": {"coingecko": "bitcoin", "ccxt": "BTC/USDT"},
    "ETH/USDT": {"coingecko": "ethereum", "ccxt": "ETH/USDT"},
    "SOL/USDT": {"coingecko": "solana", "ccxt": "SOL/USDT"},
}

TIMEFRAME_MAP = {
    "1h": {"coingecko_days": 1, "ccxt": "1h"},
    "4h": {"coingecko_days": 1, "ccxt": "4h"},
    "1d": {"coingecko_days": 365, "ccxt": "1d"},
}


class MarketDataProvider:
    """Provides OHLCV market data for dashboard charts."""

    def __init__(self):
        self.cg = CoinGeckoAPI()
        self._cache: Dict[str, dict] = {}
        self._cache_ttl = 60  # seconds

    async def get_ohlcv(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        limit: int = 100,
    ) -> List[dict]:
        """Fetch OHLCV candles as list of dicts for JSON serialization."""
        cache_key = f"{symbol}:{timeframe}"
        cached = self._cache.get(cache_key)
        if cached and (datetime.now(timezone.utc) - cached["ts"]).seconds < self._cache_ttl:
            return cached["data"]

        mapped = SYMBOL_MAP.get(symbol, {"coingecko": "bitcoin", "ccxt": symbol})
        tf = TIMEFRAME_MAP.get(timeframe, {"coingecko_days": 1, "ccxt": "1d"})

        try:
            # Try CoinGecko first (free, no key)
            df = self.cg.fetch_ohlcv(
                coin_id=mapped["coingecko"],
                days=tf["coingecko_days"],
            )
            if df.empty:
                raise ValueError("CoinGecko returned empty data")

            # Limit to last N candles
            df = df.tail(limit).reset_index()
            df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            result = df[["timestamp", "open", "high", "low", "close", "volume"]].to_dict("records")
            # Replace NaN with None for JSON serialization
            for row in result:
                for key in row:
                    if pd.isna(row[key]):
                        row[key] = None

            self._cache[cache_key] = {"data": result, "ts": datetime.now(timezone.utc)}
            return result

        except Exception as e:
            logger.warning(f"Market data fetch failed for {symbol}: {e}")
            return []

    async def get_tickers(self, symbols: List[str]) -> Dict[str, dict]:
        """Fetch current ticker info for multiple symbols."""
        try:
            ids = ",".join(SYMBOL_MAP.get(s, {"coingecko": "bitcoin"})["coingecko"] for s in symbols)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            import requests
            resp = requests.get(
                url,
                params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            result = {}
            for sym in symbols:
                cg_id = SYMBOL_MAP.get(sym, {}).get("coingecko", "bitcoin")
                info = data.get(cg_id, {})
                result[sym] = {
                    "price": info.get("usd", 0.0),
                    "change_24h_pct": info.get("usd_24h_change", 0.0) or 0.0,
                }
            return result
        except Exception as e:
            logger.warning(f"Ticker fetch failed: {e}")
            return {s: {"price": 0.0, "change_24h_pct": 0.0} for s in symbols}
