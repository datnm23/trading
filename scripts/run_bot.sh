#!/bin/bash
set -e

echo "=========================================="
echo "Hybrid Trading System — Docker Startup"
echo "Mode: ${TRADING_MODE:-paper}"
echo "=========================================="

# Ensure data dirs exist
mkdir -p /app/data/raw /app/data/processed /app/ml/models /app/journal /app/logs

# Run based on mode
if [ "${TRADING_MODE:-paper}" = "paper" ]; then
    echo "Starting paper trading bot..."
    exec python3 -m execution.live_trading --config /app/config/system.yaml --mode paper
elif [ "${TRADING_MODE:-paper}" = "live" ]; then
    echo "Starting LIVE trading bot..."
    echo "WARNING: Real money at risk!"
    exec python3 -m execution.live_trading --config /app/config/system.yaml --mode live
else
    echo "Unknown mode: ${TRADING_MODE}"
    exit 1
fi
