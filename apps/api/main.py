"""FastAPI application entry point.

Single-process modular monolith hosting all backend modules.
"""
from __future__ import annotations
import sys
import os
from contextlib import asynccontextmanager
from typing import Any

# Configure import paths before any package imports
from .path_setup import *  # noqa: F401, F403

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .routes import session, game, combat, state, bot, correction, vision
from .state_store import get_store
from .ws_manager import get_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup (Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Wire the WebSocket broadcast into the state store
    manager = get_manager()
    store = get_store()
    store.register_ws_callback(manager.broadcast)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST routers
app.include_router(session.router)
app.include_router(game.router)
app.include_router(combat.router)
app.include_router(state.router)
app.include_router(bot.router)
app.include_router(correction.router)
app.include_router(vision.router)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """Real-time push channel for a game session.

    Client connects as: ws://host/ws/{game_id}?session_id=XXX
    Server pushes typed messages: state_updated, observation_frame,
    battle_progress, phase_changed, correction_requested, error.
    """
    manager = get_manager()
    await manager.connect(game_id, websocket)
    try:
        # Send initial connection ack
        store = get_store()
        state = await store.get(game_id)
        if state:
            await websocket.send_json({
                "type": "connected",
                "game_id": game_id,
                "current_player": state.turn.current_player.value,
                "current_phase": state.turn.phase.value,
                "state_version": state.audit.state_version,
            })

        while True:
            data = await websocket.receive_text()
            # Currently read-only from server; client messages are handled via REST
            # Future: support client-initiated ping/heartbeat
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(game_id, websocket)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "version": settings.app_version}


if __name__ == "__main__":
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
