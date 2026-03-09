"""Manual correction endpoint — observation correction and referee override."""
from __future__ import annotations
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from game_schema.enums import CorrectionType, UnitStatus, Player
from ..database import get_db
from ..models import EventRecord, StateSnapshot
from ..state_store import get_store
from rules_core.phase_machine import can_advance_phase

router = APIRouter(prefix="/correction", tags=["Correction"])


class ApplyCorrectionRequest(BaseModel):
    game_id: str
    session_id: str
    actor: str
    correction_type: str   # "observation_correction" or "referee_override"
    zone_id: str
    changes: dict[str, Any]  # {unit_type: count, owner: player, ...}
    reason: str


@router.post("/apply")
async def apply_correction(
    req: ApplyCorrectionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Apply a manual correction to the game state.

    Observation corrections adjust what CV reported (no rules check needed).
    Referee overrides patch the official state (reason required, rules validated).
    """
    store = get_store()
    state = await store.get(req.game_id)
    if state is None:
        raise HTTPException(404, "Game not found.")

    correction_type = CorrectionType(req.correction_type)

    if correction_type == CorrectionType.REFEREE_OVERRIDE and not req.reason:
        raise HTTPException(400, "Referee overrides require a reason.")

    # Capture before state for audit
    zone = state.zones.get(req.zone_id)
    if zone is None:
        raise HTTPException(404, f"Zone {req.zone_id!r} not found.")

    before_snapshot = {
        "zone_id": req.zone_id,
        "owner": zone.owner.value if zone.owner else None,
        "ipc_value": zone.ipc_value,
        "unit_ids": list(zone.units),
    }

    new_version = await store.increment_version(req.game_id)
    new_state = state.model_copy(deep=True)

    # Apply changes
    new_zone = new_state.zones[req.zone_id]
    if "owner" in req.changes and req.changes["owner"] is not None:
        new_zone.owner = Player(req.changes["owner"])

    # Handle unit count adjustments
    if "add_units" in req.changes:
        for unit_type_str, count in req.changes["add_units"].items():
            from game_schema.enums import UnitType
            from game_schema.game_state import Unit
            for _ in range(count):
                uid = str(uuid.uuid4())
                owner = new_zone.owner or Player.JAPAN
                new_unit = Unit(
                    unit_id=uid,
                    unit_type=UnitType(unit_type_str),
                    owner=owner,
                    zone_id=req.zone_id,
                    status=UnitStatus.ACTIVE,
                )
                new_state.units[uid] = new_unit
                new_zone.units.append(uid)

    if "remove_units" in req.changes:
        for uid in req.changes["remove_units"]:
            if uid in new_state.units:
                new_state.units[uid].status = UnitStatus.DESTROYED
                if uid in new_zone.units:
                    new_zone.units.remove(uid)

    new_state.audit.state_version = new_version
    new_state.audit.last_modified_by = req.actor
    await store.put(req.game_id, new_state)

    after_snapshot = {
        "zone_id": req.zone_id,
        "owner": new_zone.owner.value if new_zone.owner else None,
        "ipc_value": new_zone.ipc_value,
        "unit_ids": list(new_zone.units),
    }

    event_json = {
        "event_type": correction_type.value,
        "game_id": req.game_id,
        "session_id": req.session_id,
        "actor": req.actor,
        "correction_type": correction_type.value,
        "zone_id": req.zone_id,
        "before": before_snapshot,
        "after": after_snapshot,
        "reason": req.reason,
        "state_version_before": new_version - 1,
        "state_version_after": new_version,
    }

    db.add(EventRecord(
        session_id=req.session_id,
        game_id=req.game_id,
        event_id=str(uuid.uuid4()),
        event_type=correction_type.value,
        actor=req.actor,
        state_version_before=new_version - 1,
        state_version_after=new_version,
        event_json=event_json,
    ))

    if correction_type == CorrectionType.REFEREE_OVERRIDE:
        db.add(StateSnapshot(
            session_id=req.session_id,
            game_id=req.game_id,
            state_version=new_version,
            snapshot_type="referee_override",
            player=new_state.turn.current_player.value,
            phase=new_state.turn.phase.value,
            round=new_state.turn.round,
            state_json=new_state.model_dump(mode="json"),
        ))

    return {
        "success": True,
        "correction_type": correction_type.value,
        "state_version": new_version,
        "before": before_snapshot,
        "after": after_snapshot,
    }
