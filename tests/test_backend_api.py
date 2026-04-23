"""Integration test for backend API."""

import sys
sys.path.insert(0, "/home/datnm/projects/trading")

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.api.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_strategies():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/strategies")
        assert r.status_code == 200
        data = r.json()
        assert "strategies" in data


@pytest.mark.asyncio
async def test_state():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/state")
        assert r.status_code == 200
        data = r.json()
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_rebalance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/v1/rebalance", json={
            "allocations": [
                {"strategy": "RegimeEnsemble", "weight": 0.5},
                {"strategy": "EMA-Trend", "weight": 0.5},
            ]
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "RegimeEnsemble" in data["targets"]


@pytest.mark.asyncio
async def test_market_ohlcv():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/market/ohlcv?symbol=BTC/USDT&timeframe=1d&limit=5")
        assert r.status_code == 200
        data = r.json()
        assert "candles" in data
        assert isinstance(data["candles"], list)


@pytest.mark.asyncio
async def test_market_tickers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/market/tickers")
        assert r.status_code == 200
        data = r.json()
        assert "tickers" in data
        assert "BTC/USDT" in data["tickers"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
