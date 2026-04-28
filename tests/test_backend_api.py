"""Integration test for backend API."""

import os
import sys

# Set env before any imports that depend on it
os.environ["TRADING_DB_URL"] = os.environ.get("TRADING_DB_URL", "postgresql://test:test@localhost/test")

sys.path.insert(0, "/home/datnm/projects/trading")

import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport

from backend.api.main import app, trades_service, graduation_service


@pytest.fixture(autouse=True)
def mock_backend_services(monkeypatch):
    """Mock DB-dependent services for all backend API tests."""
    fake_trades = [
        {"id": 1, "symbol": "BTC/USDT", "sub_strategy": "ema", "timestamp": "2026-04-01"},
    ]
    monkeypatch.setattr(trades_service, "get_trades", lambda **kwargs: fake_trades)
    monkeypatch.setattr(graduation_service, "compute_metrics", lambda: {
        "days_traded": 0, "days_required": 30, "return_pct": 0,
        "max_drawdown_pct": 0, "sharpe": 0, "winrate": 0,
        "trade_count": 0, "total_pnl": 0, "gates": {}, "approved": False,
        "message": "test",
    })


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


@pytest.mark.asyncio
async def test_graduation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/graduation")
        assert r.status_code == 200
        data = r.json()
        assert "gates" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
