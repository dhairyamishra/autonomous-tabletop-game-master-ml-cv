"""Session management endpoints."""
from __future__ import annotations
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from game_schema.enums import Player
from game_schema.game_state import GameState

from ..database import get_db
from ..models import GameSession
from ..state_store import get_store
from rules_core.setup import build_initial_state

router = APIRouter(prefix="/session", tags=["Session"])


class CreateSessionRequest(BaseModel):
    player_assignments: dict[str, str]  # faction -> player_name
    # e.g. {"japan": "Alice", "usa": "Bob"}


class CreateSessionResponse(BaseModel):
    session_id: str
    game_id: str
    player_assignments: dict[str, str]
    current_player: str
    current_phase: str
    current_round: int


@router.post("/create", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> CreateSessionResponse:
    """Create a new game session and initialize the game state."""
    game_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    state: GameState = build_initial_state(game_id=game_id)

    db_session = GameSession(
        id=session_id,
        game_id=game_id,
        scenario=state.scenario,
        player_assignments=request.player_assignments,
        current_player=state.turn.current_player.value,
        current_phase=state.turn.phase.value,
        current_round=state.turn.round,
    )
    db.add(db_session)

    store = get_store()
    await store.put(game_id, state)

    return CreateSessionResponse(
        session_id=session_id,
        game_id=game_id,
        player_assignments=request.player_assignments,
        current_player=state.turn.current_player.value,
        current_phase=state.turn.phase.value,
        current_round=state.turn.round,
    )


@router.get("/{session_id}", response_model=dict[str, Any])
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get session metadata."""
    from sqlalchemy import select
    result = await db.execute(select(GameSession).where(GameSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(404, f"Session {session_id} not found.")
    return {
        "session_id": session.id,
        "game_id": session.game_id,
        "scenario": session.scenario,
        "player_assignments": session.player_assignments,
        "current_player": session.current_player,
        "current_phase": session.current_phase,
        "current_round": session.current_round,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
    }
