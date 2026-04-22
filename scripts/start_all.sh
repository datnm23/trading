#!/bin/bash
# Start all Hybrid Trading System services
set -e

cd /home/datnm/projects/trading

echo "=========================================="
echo "Hybrid Trading System — Starting All"
echo "=========================================="

# 1. Start PostgreSQL
echo ""
echo "[1/4] Checking PostgreSQL..."
if ! docker ps --filter name=trading-postgres --format "{{.Names}}" | grep -q trading-postgres; then
    echo "  → Starting PostgreSQL container..."
    docker run -d \
        --name trading-postgres \
        -e POSTGRES_USER=trader \
        -e POSTGRES_PASSWORD=trading123 \
        -e POSTGRES_DB=trading_journal \
        -p 5432:5432 \
        -v ./data/postgres:/var/lib/postgresql/data \
        --restart unless-stopped \
        postgres:16-alpine 2>/dev/null || docker start trading-postgres
    sleep 3
else
    echo "  ✓ PostgreSQL already running"
fi

# 2. Start Trading Bot
echo ""
echo "[2/4] Checking Trading Bot..."
if [ -f paper_trade.pid ] && ps -p $(cat paper_trade.pid) > /dev/null 2>&1; then
    echo "  ✓ Bot already running (PID: $(cat paper_trade.pid))"
else
    echo "  → Starting paper trading bot..."
    mkdir -p logs
    nohup python3 scripts/run_paper_trade.py \
        --config config/local.yaml \
        --symbols BTC/USDT ETH/USDT SOL/USDT \
        > logs/paper_trading.log 2>&1 &
    echo $! > paper_trade.pid
    sleep 3
    echo "  ✓ Bot started (PID: $(cat paper_trade.pid))"
fi

# 3. Start Dashboard
echo ""
echo "[3/4] Checking Streamlit Dashboard..."
if [ -f dashboard.pid ] && ps -p $(cat dashboard.pid) > /dev/null 2>&1; then
    echo "  ✓ Dashboard already running (PID: $(cat dashboard.pid))"
else
    echo "  → Starting dashboard..."
    export STREAMLIT_SERVER_HEADLESS=true
    nohup streamlit run knowledge_engine/ui.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        > logs/dashboard.log 2>&1 &
    echo $! > dashboard.pid
    sleep 3
    echo "  ✓ Dashboard started (PID: $(cat dashboard.pid))"
fi

# 4. Health checks
echo ""
echo "[4/4] Health Checks..."

# Bot health
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    BOT_STATUS="✅ HEALTHY"
else
    BOT_STATUS="❌ UNREACHABLE"
fi

# Dashboard
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null | grep -q "200"; then
    DASH_STATUS="✅ HEALTHY"
else
    DASH_STATUS="❌ UNREACHABLE"
fi

# Postgres
if docker exec trading-postgres pg_isready -U trader > /dev/null 2>&1; then
    PG_STATUS="✅ HEALTHY"
else
    PG_STATUS="❌ UNREACHABLE"
fi

echo ""
echo "=========================================="
echo "STATUS SUMMARY"
echo "=========================================="
echo "PostgreSQL     : $PG_STATUS  (localhost:5432)"
echo "Trading Bot    : $BOT_STATUS  (PID: $(cat paper_trade.pid 2>/dev/null || echo N/A))"
echo "Health API     : http://localhost:8080/health"
echo "Dashboard      : $DASH_STATUS  (PID: $(cat dashboard.pid 2>/dev/null || echo N/A))"
echo "Dashboard URL  : http://localhost:8501"
echo "=========================================="

if [ "$BOT_STATUS" = "✅ HEALTHY" ] && [ "$DASH_STATUS" = "✅ HEALTHY" ] && [ "$PG_STATUS" = "✅ HEALTHY" ]; then
    echo ""
    echo "🚀 All systems operational!"
    exit 0
else
    echo ""
    echo "⚠️  Some services are not healthy. Check logs/ for details."
    exit 1
fi
