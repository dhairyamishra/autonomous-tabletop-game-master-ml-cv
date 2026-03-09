"""WebSocket connection manager.

Manages per-session client connections and broadcasts typed messages.
"""
from __future__ import annotations
import asyncio
import json
from datetime import datetime

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # game_id -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, game_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            if game_id not in self._connections:
                self._connections[game_id] = []
            self._connections[game_id].append(websocket)

    async def disconnect(self, game_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(game_id, [])
            if websocket in conns:
                conns.remove(websocket)

    async def broadcast(self, game_id: str, message: dict) -> None:
        """Send a message to all clients connected to a game session."""
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        payload = json.dumps(message)
        dead: list[WebSocket] = []

        async with self._lock:
            conns = list(self._connections.get(game_id, []))

        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        async with self._lock:
            for ws in dead:
                conns = self._connections.get(game_id, [])
                if ws in conns:
                    conns.remove(ws)

    def connection_count(self, game_id: str) -> int:
        return len(self._connections.get(game_id, []))


manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    return manager
