"""State commit endpoint — applies validated deltas to the official state."""
from __future__ import annotations
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import EventRecord, StateSnapshot
from ..state_store import get_store

router = APIRouter(prefix="/state", tags=["State"])


class CommitStateRequest(BaseModel):
    game_id: str
    session_id: str
    actor: str
    phase: str
    delta: dict[str, Any]           # zone/unit changes approved by the operator
    correction_type: str | None = None
    reason: str | None = None


@router.post("/commit")
async def commit_state(
    req: CommitStateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Apply an approved delta to the official game state."""
    store = get_store()
    state = await store.get(req.game_id)
    if state is None:
        raise HTTPException(404, "Game not found.")

    new_version = await store.increment_version(req.game_id)
    new_state = state.model_copy(deep=True)
    new_state.audit.state_version = new_version
    new_state.audit.last_modified_by = req.actor

    # Apply zone-level delta
    zones_delta: dict[str, Any] = req.delta.get("zones", {})
    for zone_id, zone_changes in zones_delta.items():
        zone = new_state.zones.get(zone_id)
        if zone:
            if "owner" in zone_changes and zone_changes["owner"] is not None:
                from game_schema.enums import Player
                zone.owner = Player(zone_changes["owner"])
            if "ipc_value" in zone_changes:
                zone.ipc_value = zone_changes["ipc_value"]
            if "has_industrial_complex" in zone_changes:
                zone.has_industrial_complex = zone_changes["has_industrial_complex"]

    # Apply unit-level delta
    units_delta: dict[str, Any] = req.delta.get("units", {})
    for unit_id, unit_changes in units_delta.items():
        unit = new_state.units.get(unit_id)
        if unit:
            if "zone_id" in unit_changes:
                unit.zone_id = unit_changes["zone_id"]
            if "status" in unit_changes:
                from game_schema.enums import UnitStatus
                unit.status = UnitStatus(unit_changes["status"])

    await store.put(req.game_id, new_state)

    # Persist snapshot
    db.add(StateSnapshot(
        session_id=req.session_id,
        game_id=req.game_id,
        state_version=new_version,
        snapshot_type=req.correction_type or "commit",
        player=new_state.turn.current_player.value,
        phase=new_state.turn.phase.value,
        round=new_state.turn.round,
        state_json=new_state.model_dump(mode="json"),
    ))

    event_type = req.correction_type or "state_committed"
    db.add(EventRecord(
        session_id=req.session_id,
        game_id=req.game_id,
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        actor=req.actor,
        state_version_before=new_version - 1,
        state_version_after=new_version,
        event_json={
            "event_type": event_type,
            "game_id": req.game_id,
            "session_id": req.session_id,
            "actor": req.actor,
            "phase": req.phase,
            "delta": req.delta,
            "reason": req.reason,
            "state_version_before": new_version - 1,
            "state_version_after": new_version,
        },
    ))

    await store.broadcast(req.game_id, {
        "type": "state_updated",
        "session_id": req.session_id,
        "game_id": req.game_id,
        "state_version": new_version,
        "current_player": new_state.turn.current_player.value,
        "current_phase": new_state.turn.phase.value,
    })

    return {
        "success": True,
        "state_version": new_version,
        "game_id": req.game_id,
    }
