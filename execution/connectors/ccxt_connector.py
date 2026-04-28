"""CCXT-based exchange connector."""

import os

import ccxt
from loguru import logger


class CCXTConnector:
    """Unified exchange connector via CCXT."""

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
    ):
        self.exchange_id = exchange_id
        self.api_key = api_key or os.getenv("EXCHANGE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("EXCHANGE_API_SECRET", "")
        self.testnet = testnet
        self.exchange: ccxt.Exchange | None = None
        self._connect()

    def _connect(self):
        try:
            cls = getattr(ccxt, self.exchange_id)
            config = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
            }
            if self.testnet:
                config["options"] = {"defaultType": "spot"}
            self.exchange = cls(config)
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
            logger.info(f"Connected to {self.exchange_id} (testnet={self.testnet})")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 500,
        since: int | None = None,
    ) -> list[list]:
        """Fetch OHLCV candles."""
        if not self.exchange:
            return []
        try:
            kwargs = {"timeframe": timeframe, "limit": limit}
            if since is not None:
                kwargs["since"] = since
            return self.exchange.fetch_ohlcv(symbol, **kwargs)
        except Exception as e:
            logger.error(f"fetch_ohlcv error: {e}")
            return []

    def create_market_order(self, symbol: str, side: str, amount: float) -> dict | None:
        """Place a market order."""
        if not self.exchange:
            return None
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            logger.info(
                f"Order placed: {side} {amount} {symbol} @ {order.get('average', 'market')}"
            )
            return order
        except Exception as e:
            logger.error(f"Order error: {e}")
            return None

    def fetch_balance(self) -> dict:
        if not self.exchange:
            return {}
        return self.exchange.fetch_balance()

    def fetch_positions(self) -> list[dict]:
        if not self.exchange:
            return []
        try:
            return self.exchange.fetch_positions()
        except Exception:
            return []

    def fetch_ticker(self, symbol: str) -> dict | None:
        """Fetch real-time ticker (last price, bid, ask, volume)."""
        if not self.exchange:
            return None
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"fetch_ticker error: {e}")
            return None
