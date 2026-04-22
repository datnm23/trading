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
        self.connector = CCXTConnector(exchange_id=exchange_id, testnet=False)

    def fetch(self, symbol: str, timeframe: str = "1d", limit: int = 1000, use_cache: bool = True) -> pd.DataFrame:
        """Fetch OHLCV as DataFrame."""
        cache_file = self.data_dir / f"{symbol.replace('/', '_')}_{timeframe}.csv"

        if use_cache and cache_file.exists():
            logger.info(f"Loading cached data: {cache_file}")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return df

        logger.info(f"Downloading {symbol} {timeframe} from {self.connector.exchange_id}")
        ohlcv = self.connector.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv:
            logger.warning("No data returned")
            return pd.DataFrame()

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        if use_cache:
            df.to_csv(cache_file)
            logger.info(f"Saved cache: {cache_file}")

        return df
