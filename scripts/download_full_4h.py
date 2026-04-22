#!/usr/bin/env python3
"""Download full BTC/USDT 4h history from Binance via CCXT forward pagination."""

import sys
sys.path.insert(0, "/home/datnm/projects/trading")

import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
import ccxt


def download_full_4h(symbol: str = "BTC/USDT", timeframe: str = "4h", start_date: str = "2023-07-27"):
    """Paginate forwards to fetch all 4h candles from start_date to now."""
    exchange = ccxt.binance({"enableRateLimit": True})
    start_ts = int(pd.Timestamp(start_date, tz="UTC").timestamp() * 1000)
    now_ts = int(pd.Timestamp.now(tz="UTC").timestamp() * 1000)

    all_ohlcv = []
    since = start_ts

    while since < now_ts:
        logger.info(f"Fetching {symbol} {timeframe} since={pd.Timestamp(since, unit='ms')}")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not ohlcv:
            logger.warning("No more data returned")
            break

        # Only keep candles we haven't seen yet
        new_candles = [c for c in ohlcv if c[0] >= since]
        if not new_candles:
            logger.warning("No new candles in batch, breaking")
            break

        all_ohlcv.extend(new_candles)
        newest_ts = new_candles[-1][0]
        logger.info(f"  Got {len(new_candles)} candles | newest={pd.Timestamp(newest_ts, unit='ms')}")

        if newest_ts == since:
            logger.warning("Stuck at same timestamp, breaking")
            break

        since = newest_ts + 1

    if not all_ohlcv:
        raise ValueError("No data downloaded")

    df = pd.DataFrame(all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="last")].sort_index()

    out_path = Path(f"/home/datnm/projects/trading/data/raw/{symbol.replace('/', '_')}_{timeframe}.csv")
    df.to_csv(out_path)
    logger.info(f"Saved {len(df)} bars to {out_path} | {df.index[0]} to {df.index[-1]}")
    return df


if __name__ == "__main__":
    download_full_4h()
