"""Socket.IO manager — broadcasts state to all connected clients."""

import asyncio
import json
import os
from datetime import datetime

import socketio
from loguru import logger

from backend.api.aggregator import StateAggregator


def _serialize_datetime(obj):
    """Helper to serialize datetime objects for JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Restrict Socket.IO CORS to known origins
_socket_cors = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
).split(",")
_socket_cors = [o.strip() for o in _socket_cors if o.strip()]


class SocketManager:
    """Manages Socket.IO connections and broadcasts."""

    def __init__(self, aggregator: StateAggregator, broadcast_interval: float = 5.0):
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=_socket_cors,
            json=json,  # use standard json with custom default
        )
        self.aggregator = aggregator
        self.broadcast_interval = broadcast_interval
        self._clients: set[str] = set()
        self._running = False

        # Register event handlers
        self.sio.on("connect")(self._on_connect)
        self.sio.on("disconnect")(self._on_disconnect)
        self.sio.on("subscribe")(self._on_subscribe)

    async def _on_connect(self, sid, environ, auth=None):
        """Handle client connection."""
        logger.info(f"Client connected: {sid}")
        self._clients.add(sid)
        # Send initial state immediately (serialize first)
        state = self._get_serializable_state()
        await self.sio.emit("state_update", state, room=sid)

    async def _on_disconnect(self, sid):
        """Handle client disconnection."""
        logger.info(f"Client disconnected: {sid}")
        self._clients.discard(sid)

    async def _on_subscribe(self, sid, data):
        """Handle subscription request."""
        channel = data.get("channel", "all") if isinstance(data, dict) else "all"
        logger.debug(f"Client {sid} subscribed to {channel}")
        await self.sio.enter_room(sid, channel)

    def _get_serializable_state(self):
        """Get state with all datetime objects converted to strings."""
        state = self.aggregator.get_state()
        return json.loads(json.dumps(state, default=_serialize_datetime))

    async def broadcast_loop(self):
        """Broadcast state to all clients periodically."""
        self._running = True
        while self._running:
            if self._clients:
                try:
                    state = self._get_serializable_state()
                    await self.sio.emit("state_update", state)
                    logger.debug(f"Broadcasted state to {len(self._clients)} clients")
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
            await asyncio.sleep(self.broadcast_interval)

    def stop(self):
        self._running = False

    def get_app(self):
        """Return ASGI app for mounting with FastAPI."""
        return socketio.ASGIApp(self.sio)
