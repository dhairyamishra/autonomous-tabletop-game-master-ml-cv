"""Game state and phase management endpoints."""
from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from game_schema.enums import Phase, Player, UnitType
from game_schema.game_state import GameState

from ..database import get_db
from ..models import EventRecord, GameSession, StateSnapshot
from ..state_store import get_store
from rules_core.economy import PurchaseItem, validate_purchase, collect_income
from rules_core.movement import MoveRequest, validate_move, validate_placement
from rules_core.phase_machine import advance_phase

router = APIRouter(prefix="/game", tags=["Game"])


async def _require_state(game_id: str) -> GameState:
    store = get_store()
    state = await store.get(game_id)
    if state is None:
        raise HTTPException(404, f"Game {game_id} not found. Is the session loaded?")
    return state


# ── GET /game/{id}/state ──────────────────────────────────────────────────────

@router.get("/{game_id}/state")
async def get_state(game_id: str) -> dict[str, Any]:
    state = await _require_state(game_id)
    return state.model_dump()


# ── GET /game/{id}/events ─────────────────────────────────────────────────────

@router.get("/{game_id}/events")
async def get_events(
    game_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(EventRecord)
        .where(EventRecord.game_id == game_id)
        .order_by(EventRecord.created_at)
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()
    return [r.event_json for r in records]


# ── GET /game/{id}/replay ─────────────────────────────────────────────────────

@router.get("/{game_id}/replay")
async def get_replay(
    game_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    snapshots_q = await db.execute(
        select(StateSnapshot)
        .where(StateSnapshot.game_id == game_id)
        .order_by(StateSnapshot.state_version)
    )
    events_q = await db.execute(
        select(EventRecord)
        .where(EventRecord.game_id == game_id)
        .order_by(EventRecord.created_at)
    )
    snapshots = [s.state_json for s in snapshots_q.scalars().all()]
    events = [e.event_json for e in events_q.scalars().all()]
    return {"game_id": game_id, "snapshots": snapshots, "events": events}


# ── POST /action/validate ─────────────────────────────────────────────────────

class ValidateActionRequest(BaseModel):
    game_id: str
    player: str
    action_type: str   # "move", "purchase", "place"
    unit_id: str | None = None
    to_zone: str | None = None
    unit_type: str | None = None
    purchases: list[dict[str, Any]] | None = None


@router.post("/action/validate")
async def validate_action(req: ValidateActionRequest) -> dict[str, Any]:
    state = await _require_state(req.game_id)
    player = Player(req.player)
    phase = state.turn.phase

    if req.action_type == "move" and req.unit_id and req.to_zone:
        result = validate_move(state, player, phase, MoveRequest(
            unit_id=req.unit_id,
            to_zone=req.to_zone,
        ))
        return {"is_legal": result.is_legal, "reason": result.reason}

    if req.action_type == "purchase" and req.purchases:
        items = [PurchaseItem(unit_type=UnitType(p["unit_type"]), count=p["count"]) for p in req.purchases]
        result = validate_purchase(state, player, items)
        return {"is_legal": result.is_legal, "reason": result.reason, "total_cost": result.total_cost}

    if req.action_type == "place" and req.unit_type and req.to_zone:
        result = validate_placement(state, player, UnitType(req.unit_type), req.to_zone)
        return {"is_legal": result.is_legal, "reason": result.reason}

    return {"is_legal": False, "reason": "Unknown action type or missing fields."}


# ── POST /phase/advance ───────────────────────────────────────────────────────

class AdvancePhaseRequest(BaseModel):
    game_id: str
    session_id: str
    actor: str


@router.post("/phase/advance")
async def advance_phase_endpoint(
    req: AdvancePhaseRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    state = await _require_state(req.game_id)
    transition = advance_phase(state)
    if not transition.success:
        raise HTTPException(400, transition.reason)

    store = get_store()
    new_version = await store.increment_version(req.game_id)

    old_phase = state.turn.phase
    old_player = state.turn.current_player

    new_state = state.model_copy(deep=True)
    new_state.turn.phase = transition.new_phase
    new_state.turn.current_player = transition.new_player
    if transition.new_round:
        new_state.turn.round = transition.new_round
    new_state.audit.state_version = new_version
    new_state.audit.last_modified_by = req.actor

    await store.put(req.game_id, new_state)

    # Persist event
    event_data = {
        "event_type": "phase_advanced",
        "game_id": req.game_id,
        "session_id": req.session_id,
        "actor": req.actor,
        "from_phase": old_phase.value,
        "to_phase": transition.new_phase.value,
        "player": old_player.value,
        "state_version_before": new_version - 1,
        "state_version_after": new_version,
    }
    db.add(EventRecord(
        session_id=req.session_id,
        game_id=req.game_id,
        event_id=str(__import__("uuid").uuid4()),
        event_type="phase_advanced",
        actor=req.actor,
        state_version_before=new_version - 1,
        state_version_after=new_version,
        event_json=event_data,
    ))

    # Update session metadata
    result = await db.execute(select(GameSession).where(GameSession.game_id == req.game_id))
    session = result.scalar_one_or_none()
    if session:
        session.current_phase = transition.new_phase.value
        session.current_player = transition.new_player.value
        if transition.new_round:
            session.current_round = transition.new_round

    # Broadcast WebSocket message
    await store.broadcast(req.game_id, {
        "type": "phase_changed",
        "session_id": req.session_id,
        "game_id": req.game_id,
        "round": new_state.turn.round,
        "player": transition.new_player.value,
        "phase": transition.new_phase.value,
        "state_version": new_version,
    })

    return {
        "success": True,
        "new_phase": transition.new_phase.value,
        "new_player": transition.new_player.value,
        "new_round": new_state.turn.round,
        "state_version": new_version,
    }
