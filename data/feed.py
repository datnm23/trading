"""Data feed: download and cache market data."""

from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from execution.connectors.ccxt_connector import CCXTConnector


class DataFeed:
    """Download and cache OHLCV data from exchange."""

    def __init__(self, data_dir: str = "./data/raw", exchange_id: str = "binance"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.connector = CCXTConnector(exchange_id=exchange_id, testnet=True)

    def fetch(self, symbol: str, timeframe: str = "1d", limit: int = 1000, use_cache: bool = True) -> pd.DataFrame:
        """Fetch OHLCV as DataFrame. Merges cache with live data if cache is stale."""
        cache_file = self.data_dir / f"{symbol.replace('/', '_')}_{timeframe}.csv"
        df_cache = None

        if use_cache and cache_file.exists():
            df_cache = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            # Check freshness — stale if past expected next bar + 30min buffer
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            now = pd.Timestamp.utcnow().tz_localize(None)
            last = df_cache.index[-1]
            if last.tzinfo is not None:
                last = last.tz_localize(None)
            # Next bar should arrive within timeframe + 30min buffer after last bar
            stale_threshold = pd.Timedelta(minutes=timeframe_minutes + 30)
            if not df_cache.empty and (now - last) <= stale_threshold:
                logger.info(f"Loading fresh cached data: {cache_file}")
                return df_cache
            logger.info(f"Cache stale ({df_cache.index[-1]}), refreshing from {self.connector.exchange_id}")

        logger.info(f"Downloading {symbol} {timeframe} from {self.connector.exchange_id}")
        since_ms = None
        if df_cache is not None and not df_cache.empty:
            since_ms = int(df_cache.index[-1].timestamp() * 1000) + 1
        ohlcv = self.connector.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since_ms)
        if not ohlcv:
            logger.warning("No data returned")
            return df_cache if df_cache is not None else pd.DataFrame()

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        if df_cache is not None and not df_cache.empty:
            df = pd.concat([df_cache, df])
            df = df[~df.index.duplicated(keep="last")]
            df.sort_index(inplace=True)

        if use_cache:
            df.to_csv(cache_file)
            logger.info(f"Saved cache: {cache_file} ({len(df)} rows)")

        return df

    @staticmethod
    def _timeframe_to_minutes(timeframe: str) -> int:
        """Convert timeframe string (e.g. '4h', '1d') to minutes."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        multipliers = {"m": 1, "h": 60, "d": 1440, "w": 10080}
        return value * multipliers.get(unit, 1)
