"""FastAPI gateway — unified API + Socket.IO for Next.js frontend."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from loguru import logger

from backend.api.aggregator import StateAggregator
from backend.api.socket_manager import SocketManager
from backend.api.market_data import MarketDataProvider
from backend.api.trades_service import TradesService
from backend.api.graduation_service import GraduationService
from backend.api.auth import verify_read_key, verify_admin_key
from knowledge_engine.rag import WikiRAG


market_provider = MarketDataProvider()
trades_service = TradesService()
wiki_rag = WikiRAG()
graduation_service = GraduationService()


class AllocationItem(BaseModel):
    strategy: str
    weight: float


class RebalanceRequest(BaseModel):
    allocations: List[AllocationItem]


class WikiSearchRequest(BaseModel):
    query: str
    top_k: int = 5


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

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# CORS — restrict to known origins
cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Mount Socket.IO
app.mount("/socket.io", socket_manager.get_app())


@app.get("/health")
async def health_check():
    return {"status": "healthy", "gateway": True}


@app.get("/api/v1/strategies", dependencies=[Depends(verify_read_key)])
async def get_strategies():
    return {
        "strategies": [s.model_dump() for s in aggregator.strategies.values()],
        "timestamp": aggregator.get_state()["timestamp"],
    }


@app.get("/api/v1/state", dependencies=[Depends(verify_read_key)])
async def get_full_state():
    return aggregator.get_state()


@app.get("/api/v1/trades", dependencies=[Depends(verify_read_key)])
async def get_trades(
    sub_strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
):
    """Fetch closed trade history with sub-strategy breakdown.

    Only returns trades that have sub-strategy metadata (new trades).
    """
    try:
        trades = trades_service.get_trades(
            sub_strategy=sub_strategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Trades fetch failed: {e}")
        return {"trades": [], "count": 0, "error": str(e)}


@app.get("/api/v1/trades/export", dependencies=[Depends(verify_read_key)])
async def export_trades(
    format: str = "csv",
    sub_strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Export trades to CSV or JSON."""
    try:
        trades = trades_service.get_trades(
            sub_strategy=sub_strategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )
        if format == "json":
            return {"trades": trades, "count": len(trades)}
        else:
            # CSV format
            import csv
            import io
            output = io.StringIO()
            if trades:
                writer = csv.DictWriter(output, fieldnames=trades[0].keys())
                writer.writeheader()
                writer.writerows(trades)
            return {"csv": output.getvalue(), "count": len(trades)}
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return {"error": str(e)}


@app.post("/api/v1/rebalance", dependencies=[Depends(verify_admin_key)])
async def rebalance_portfolio(req: RebalanceRequest):
    """Store rebalance targets for strategies.

    Requires admin key. In a production system, this would trigger actual
    capital reallocation across strategy accounts.
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


@app.get("/api/v1/rebalance", dependencies=[Depends(verify_read_key)])
async def get_rebalance_targets():
    return {"targets": rebalance_targets}


@app.get("/api/v1/market/ohlcv", dependencies=[Depends(verify_read_key)])
async def get_market_ohlcv(symbol: str = "BTC/USDT", timeframe: str = "1d", limit: int = 100):
    """Fetch OHLCV candles for a symbol."""
    try:
        data = await market_provider.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        return {"symbol": symbol, "timeframe": timeframe, "candles": data}
    except Exception as e:
        logger.error(f"OHLCV fetch failed: {e}")
        return {"symbol": symbol, "timeframe": timeframe, "candles": [], "error": str(e)}


@app.get("/api/v1/market/tickers", dependencies=[Depends(verify_read_key)])
async def get_market_tickers():
    """Fetch current prices and 24h change for tracked symbols."""
    try:
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        data = await market_provider.get_tickers(symbols)
        return {"tickers": data, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Ticker fetch failed: {e}")
        return {"tickers": {}, "timestamp": datetime.utcnow().isoformat(), "error": str(e)}


@app.get("/api/v1/graduation", dependencies=[Depends(verify_read_key)])
async def get_graduation_status():
    """Return paper trading graduation progress."""
    try:
        metrics = graduation_service.compute_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Graduation status failed: {e}")
        return {
            "days_traded": 0,
            "days_required": 30,
            "return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe": 0.0,
            "winrate": 0.0,
            "trade_count": 0,
            "total_pnl": 0.0,
            "gates": {},
            "approved": False,
            "message": f"Error: {e}",
        }


@app.post("/api/v1/wiki/search", dependencies=[Depends(verify_read_key)])
async def wiki_search(req: WikiSearchRequest):
    """Search Turtle Trading Wiki concepts via RAG.

    Returns top-k matching concepts with relevance scores.
    """
    try:
        results = wiki_rag.search(req.query)
        # Limit to requested top_k
        results = results[: req.top_k]
        return {
            "query": req.query,
            "results": [
                {
                    "id": r["document"]["id"],
                    "title": r["document"]["title"],
                    "source_url": r["document"].get("source_url", ""),
                    "content_preview": r["document"]["content"][:500],
                    "relevance": round(r["score"], 4),
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Wiki search failed: {e}")
        return {"query": req.query, "results": [], "count": 0, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8090, reload=True)
