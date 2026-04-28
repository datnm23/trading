"""Tests for /api/v1/trades, /api/v1/trades/export, and /api/v1/wiki/search endpoints."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Must set env before importing main
os.environ["TRADING_DB_URL"] = "postgresql://test:test@localhost/test"
os.environ["API_KEY"] = "test-read-key"
os.environ["ADMIN_KEY"] = "test-admin-key"

from httpx import AsyncClient, ASGITransport
from backend.api.main import app, trades_service, wiki_rag

READ_HEADERS = {"X-API-Key": "test-read-key"}


@pytest.fixture(autouse=True)
def mock_trades_service(monkeypatch):
    """Mock TradesService to avoid real DB calls."""
    fake_trades = [
        {
            "id": 1,
            "timestamp": "2026-04-01T10:00:00",
            "symbol": "BTC/USDT",
            "side": "sell",
            "entry_price": 50000.0,
            "exit_price": 52000.0,
            "size": 0.1,
            "pnl": 200.0,
            "pnl_pct": 4.0,
            "holding_bars": 12,
            "exit_reason": "crossover_down",
            "stop_price": 48000.0,
            "target_price": None,
            "sub_strategy": "ema",
            "regime": "trending",
        },
        {
            "id": 2,
            "timestamp": "2026-04-02T10:00:00",
            "symbol": "ETH/USDT",
            "side": "sell",
            "entry_price": 3000.0,
            "exit_price": 2900.0,
            "size": 1.0,
            "pnl": -100.0,
            "pnl_pct": -3.33,
            "holding_bars": 8,
            "exit_reason": "breakdown",
            "stop_price": 2800.0,
            "target_price": None,
            "sub_strategy": "breakout",
            "regime": "trending",
        },
    ]

    def fake_get_trades(**kwargs):
        result = list(fake_trades)
        if kwargs.get("sub_strategy"):
            result = [t for t in result if t["sub_strategy"] == kwargs["sub_strategy"]]
        if kwargs.get("symbol"):
            result = [t for t in result if t["symbol"] == kwargs["symbol"]]
        if kwargs.get("start_date"):
            result = [t for t in result if t["timestamp"] >= kwargs["start_date"]]
        if kwargs.get("end_date"):
            result = [t for t in result if t["timestamp"] <= kwargs["end_date"]]
        return result[: kwargs.get("limit", 50)]

    monkeypatch.setattr(trades_service, "get_trades", fake_get_trades)
    return fake_trades


@pytest.mark.asyncio
async def test_get_trades_no_key_403():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades")
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_trades_default():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "trades" in data
        assert "count" in data
        assert data["count"] == 2
        assert data["trades"][0]["symbol"] == "BTC/USDT"


@pytest.mark.asyncio
async def test_get_trades_filter_sub_strategy():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades?sub_strategy=ema", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["trades"][0]["sub_strategy"] == "ema"


@pytest.mark.asyncio
async def test_get_trades_filter_symbol():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades?symbol=ETH/USDT", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["trades"][0]["symbol"] == "ETH/USDT"


@pytest.mark.asyncio
async def test_get_trades_filter_date_range():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades?start_date=2026-04-02T00:00:00", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["trades"][0]["timestamp"].startswith("2026-04-02")


@pytest.mark.asyncio
async def test_get_trades_limit():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades?limit=1", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1


@pytest.mark.asyncio
async def test_export_trades_csv():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades/export?format=csv", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "csv" in data
        assert "count" in data
        assert data["count"] == 2
        csv_content = data["csv"]
        assert "symbol" in csv_content
        assert "BTC/USDT" in csv_content
        assert "ETH/USDT" in csv_content


@pytest.mark.asyncio
async def test_export_trades_json():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades/export?format=json", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "trades" in data
        assert data["count"] == 2


@pytest.mark.asyncio
async def test_export_trades_filter():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades/export?format=csv&sub_strategy=breakout", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert "breakout" in data["csv"]


@pytest.mark.asyncio
async def test_trades_empty_result():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/trades?sub_strategy=grid", headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 0
        assert data["trades"] == []


@pytest.mark.asyncio
async def test_wiki_search():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/v1/wiki/search", json={"query": "trend following", "top_k": 3}, headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data
        # WikiRAG has 683 documents indexed, should return results
        assert data["count"] > 0
        first = data["results"][0]
        assert "id" in first
        assert "title" in first
        assert "relevance" in first
        assert "content_preview" in first


@pytest.mark.asyncio
async def test_wiki_search_empty_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/v1/wiki/search", json={"query": "", "top_k": 3}, headers=READ_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 0  # may return 0 or random results for empty query
