"""Lightweight health check HTTP server for Docker/monitoring.

Runs in a background thread and exposes:
    GET /health   -> JSON status of trading engine
    GET /metrics  -> Simple text metrics
"""

import json
import threading
from collections.abc import Callable
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from loguru import logger


class _HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health endpoints."""

    def __init__(self, *args, status_provider=None, **kwargs):
        self._status_provider = status_provider
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        # Suppress default logging
        pass

    def do_GET(self):
        if self.path == "/health":
            self._send_json(self._get_health())
        elif self.path == "/metrics":
            self._send_text(self._get_metrics())
        else:
            self.send_response(404)
            self.end_headers()

    def _get_health(self) -> dict:
        provider = self._status_provider
        if provider:
            status = provider()
            healthy = status.get("running", False)
            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "data": status,
            }
        return {"status": "unknown", "timestamp": datetime.now().isoformat()}

    def _get_metrics(self) -> str:
        provider = self._status_provider
        if not provider:
            return "# No status provider\n"
        status = provider()
        equity = status.get("equity", 0)
        capital = status.get("capital", 0)
        open_pos = status.get("open_positions", 0)
        running = 1 if status.get("running", False) else 0
        dd = status.get("drawdown", 0) or 0
        lines = [
            "# HELP trading_equity Current account equity",
            "# TYPE trading_equity gauge",
            f"trading_equity {equity}",
            "",
            "# HELP trading_capital Current cash capital",
            "# TYPE trading_capital gauge",
            f"trading_capital {capital}",
            "",
            "# HELP trading_positions_open Number of open positions",
            "# TYPE trading_positions_open gauge",
            f"trading_positions_open {open_pos}",
            "",
            "# HELP trading_running Whether the bot is running (1) or not (0)",
            "# TYPE trading_running gauge",
            f"trading_running {running}",
            "",
            "# HELP trading_drawdown Current drawdown percentage",
            "# TYPE trading_drawdown gauge",
            f"trading_drawdown {dd}",
        ]
        return "\n".join(lines) + "\n"

    def _send_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _send_text(self, text: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(text.encode())


class HealthServer:
    """Background HTTP server for health checks."""

    def __init__(
        self, port: int = 8080, status_provider: Callable[[], dict] | None = None
    ):
        self.port = port
        self.status_provider = status_provider
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        self._server = HTTPServer(
            ("0.0.0.0", self.port),
            lambda *args, **kwargs: _HealthHandler(
                *args, status_provider=self.status_provider, **kwargs
            ),
        )
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Health server started on port {self.port}")

    def stop(self):
        if self._server:
            self._server.shutdown()
            logger.info("Health server stopped")


if __name__ == "__main__":
    # Demo
    def demo_status():
        return {
            "running": True,
            "equity": 105000.0,
            "capital": 95000.0,
            "open_positions": 1,
            "mode": "paper",
        }

    server = HealthServer(port=8080, status_provider=demo_status)
    server.start()
    import time

    time.sleep(60)
