"""In-process state store.

Holds live GameState objects keyed by game_id for fast in-process access.
PostgreSQL is used for persistence and replay; this is the hot cache.
"""
from __future__ import annotations
import asyncio
from typing import Callable, Awaitable

from game_schema.game_state import GameState


class StateStore:
    """Thread-safe in-memory store for active game states."""

    def __init__(self) -> None:
        self._states: dict[str, GameState] = {}
        self._lock = asyncio.Lock()
        self._version_counters: dict[str, int] = {}
        self._ws_callbacks: list[Callable[[str, dict], Awaitable[None]]] = []

    async def get(self, game_id: str) -> GameState | None:
        async with self._lock:
            return self._states.get(game_id)

    async def put(self, game_id: str, state: GameState) -> None:
        async with self._lock:
            self._states[game_id] = state

    async def increment_version(self, game_id: str) -> int:
        async with self._lock:
            v = self._version_counters.get(game_id, 0) + 1
            self._version_counters[game_id] = v
            return v

    def register_ws_callback(self, cb: Callable[[str, dict], Awaitable[None]]) -> None:
        self._ws_callbacks.append(cb)

    async def broadcast(self, game_id: str, message: dict) -> None:
        for cb in self._ws_callbacks:
            try:
                await cb(game_id, message)
            except Exception:
                pass


_store = StateStore()


def get_store() -> StateStore:
    return _store
