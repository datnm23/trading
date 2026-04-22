"""FastAPI gateway — unified API + Socket.IO for Next.js frontend."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from backend.api.aggregator import StateAggregator
from backend.api.socket_manager import SocketManager
from backend.api.market_data import MarketDataProvider


market_provider = MarketDataProvider()


class AllocationItem(BaseModel):
    strategy: str
    weight: float


class RebalanceRequest(BaseModel):
    allocations: List[AllocationItem]


# Global instances
aggregator = StateAggregator(poll_interval=5.0)
socket_manager = SocketManager(aggregator, broadcast_interval=5.0)

# Rebalance targets stored in memory
rebalance_targets: Dict[str, float] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup."""
    logger.info("Starting API Gateway...")

    # Start background loops
    poll_task = asyncio.create_task(aggregator.run_loop())
    broadcast_task = asyncio.create_task(socket_manager.broadcast_loop())

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")
    socket_manager.stop()
    aggregator.stop()
    poll_task.cancel()
    broadcast_task.cancel()
    try:
        await poll_task
        await broadcast_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Hybrid Trading Gateway",
    description="Unified API + Socket.IO for trading dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
app.mount("/socket.io", socket_manager.get_app())


@app.get("/health")
async def health_check():
    return {"status": "healthy", "gateway": True}


@app.get("/api/v1/strategies")
async def get_strategies():
    return {
        "strategies": [s.model_dump() for s in aggregator.strategies.values()],
        "timestamp": aggregator.get_state()["timestamp"],
    }


@app.get("/api/v1/state")
async def get_full_state():
    return aggregator.get_state()


@app.post("/api/v1/rebalance")
async def rebalance_portfolio(req: RebalanceRequest):
    """Store rebalance targets for strategies.

    In a production system, this would trigger actual capital reallocation
    across strategy accounts. For paper trading, we store targets and
    expose them via the health endpoint for bots to read.
    """
    global rebalance_targets
    for alloc in req.allocations:
        if alloc.strategy:
            rebalance_targets[alloc.strategy] = alloc.weight
    logger.info(f"Rebalance targets updated: {rebalance_targets}")
    return {
        "status": "ok",
        "targets": rebalance_targets,
        "message": "Rebalance targets stored. Bots will adjust on next cycle.",
    }


@app.get("/api/v1/rebalance")
async def get_rebalance_targets():
    return {"targets": rebalance_targets}


@app.get("/api/v1/market/ohlcv")
async def get_market_ohlcv(symbol: str = "BTC/USDT", timeframe: str = "1d", limit: int = 100):
    """Fetch OHLCV candles for a symbol."""
    data = await market_provider.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    return {"symbol": symbol, "timeframe": timeframe, "candles": data}


@app.get("/api/v1/market/tickers")
async def get_market_tickers():
    """Fetch current prices and 24h change for tracked symbols."""
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    data = await market_provider.get_tickers(symbols)
    return {"tickers": data, "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8090, reload=True)
