#!/bin/bash
set -e

echo "=========================================="
echo "Hybrid Trading System — Docker Startup"
echo "Service: ${SERVICE_MODE:-bot}"
echo "=========================================="

# Ensure data dirs exist
mkdir -p /app/data/raw /app/data/processed /app/data/exports /app/data/logs /app/journal /app/logs

# Run based on service mode
case "${SERVICE_MODE:-bot}" in
    bot)
        echo "Starting trading bot..."
        exec python3 -m execution.live_trading \
            --config /app/config/system.yaml \
            --mode "${TRADING_MODE:-paper}"
        ;;
    api)
        echo "Starting backend API server..."
        exec uvicorn backend.api.main:app \
            --host 0.0.0.0 \
            --port 8090 \
            --workers 1
        ;;
    export)
        echo "Starting export cron job..."
        echo "0 10 * * * /opt/venv/bin/python /app/scripts/export_journal.py --output-dir /app/data/exports --format both >> /app/data/logs/export.log 2>&1" | crontab -
        exec crond -f
        ;;
    *)
        echo "Unknown SERVICE_MODE: ${SERVICE_MODE}"
        echo "Valid modes: bot, api, export"
        exit 1
        ;;
esac
