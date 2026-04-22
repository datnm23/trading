"""Lightweight health check HTTP server for Docker/monitoring.

Runs in a background thread and exposes:
    GET /health   -> JSON status of trading engine
    GET /metrics  -> Simple text metrics
"""

import json
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable

from loguru import logger


class _HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health endpoints."""

    _status_provider: Optional[Callable[[], dict]] = None

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
        provider = type(self)._status_provider
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
        provider = type(self)._status_provider
        if not provider:
            return "# No status provider\n"
        status = provider()
        lines = [
            f"equity {status.get('equity', 0)}",
            f"capital {status.get('capital', 0)}",
            f"open_positions {status.get('open_positions', 0)}",
            f"running {1 if status.get('running', False) else 0}",
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

    def __init__(self, port: int = 8080, status_provider: Optional[Callable[[], dict]] = None):
        self.port = port
        self.status_provider = status_provider
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        _HealthHandler._status_provider = self.status_provider
        self._server = HTTPServer(("0.0.0.0", self.port), _HealthHandler)
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
