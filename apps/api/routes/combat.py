"""Combat resolution endpoint."""
from __future__ import annotations
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from game_schema.enums import BattleStatus, UnitStatus
from game_schema.game_state import GameState

from ..database import get_db
from ..models import BattleLog, EventRecord
from ..state_store import get_store
from battle_core.resolution import BattleChoices, resolve_battle
from battle_core.rng import RngStream

router = APIRouter(prefix="/combat", tags=["Combat"])


class ResolveCombatRequest(BaseModel):
    game_id: str
    session_id: str
    actor: str
    battle_id: str
    casualty_policy: str = "cheapest_first"
    retreat_after_round: int | None = None
    retreat_to_zone: str | None = None


@router.post("/resolve")
async def resolve_combat(
    req: ResolveCombatRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resolve a single pending battle using server-side RNG."""
    store = get_store()
    state = await store.get(req.game_id)
    if state is None:
        raise HTTPException(404, "Game not found.")

    battle = state.pending_battles.get(req.battle_id)
    if battle is None:
        raise HTTPException(404, f"Battle {req.battle_id} not found.")
    if battle.status not in (BattleStatus.PENDING, BattleStatus.IN_PROGRESS):
        raise HTTPException(400, f"Battle {req.battle_id} is already resolved ({battle.status}).")

    rng = RngStream.from_new_seed()
    choices = BattleChoices(
        retreat_after_round=req.retreat_after_round,
        retreat_to_zone=req.retreat_to_zone,
    )

    result = resolve_battle(state, battle, choices, rng)

    # Apply result to state
    new_state = state.model_copy(deep=True)
    new_version = await store.increment_version(req.game_id)

    # Mark casualties
    for uid in result.all_attacker_losses:
        if uid in new_state.units:
            new_state.units[uid].status = UnitStatus.DESTROYED

    for uid in result.all_defender_losses:
        if uid in new_state.units:
            new_state.units[uid].status = UnitStatus.DESTROYED

    # Update battle status
    pb = new_state.pending_battles[req.battle_id]
    pb.status = result.status
    pb.rng_seed = result.rng_seed
    pb.rng_algorithm = result.rng_algorithm
    pb.battle_input_hash = result.battle_input_hash

    # Territory capture
    if result.territory_captured:
        zone = new_state.zones.get(result.zone_id)
        if zone:
            zone.owner = battle.attacker

    new_state.audit.state_version = new_version
    new_state.audit.last_modified_by = req.actor

    await store.put(req.game_id, new_state)

    # Persist battle log
    db.add(BattleLog(
        session_id=req.session_id,
        game_id=req.game_id,
        battle_id=req.battle_id,
        zone_id=result.zone_id,
        attacker=result.attacker.value,
        defender=result.defender.value,
        status=result.status.value,
        rng_seed=result.rng_seed,
        rng_algorithm=result.rng_algorithm,
        battle_input_hash=result.battle_input_hash,
        result_json=result.to_dict(),
    ))

    event_data = {
        "event_type": "battle_resolved",
        "game_id": req.game_id,
        "session_id": req.session_id,
        "actor": req.actor,
        "battle_id": req.battle_id,
        "zone_id": result.zone_id,
        "status": result.status.value,
        "total_rounds": len(result.rounds),
        "attacker_losses": result.all_attacker_losses,
        "defender_losses": result.all_defender_losses,
        "territory_captured": result.territory_captured,
        "state_version_before": new_version - 1,
        "state_version_after": new_version,
    }
    db.add(EventRecord(
        session_id=req.session_id,
        game_id=req.game_id,
        event_id=str(uuid.uuid4()),
        event_type="battle_resolved",
        actor=req.actor,
        state_version_before=new_version - 1,
        state_version_after=new_version,
        event_json=event_data,
    ))

    # Broadcast per-round results
    for rnd in result.rounds:
        await store.broadcast(req.game_id, {
            "type": "battle_progress",
            "session_id": req.session_id,
            "game_id": req.game_id,
            "battle_id": req.battle_id,
            "zone_id": result.zone_id,
            "round_number": rnd.round_number,
            "attacker_rolls": rnd.attacker_rolls,
            "defender_rolls": rnd.defender_rolls,
            "attacker_hits": rnd.attacker_hits,
            "defender_hits": rnd.defender_hits,
            "attacker_remaining": rnd.attacker_remaining,
            "defender_remaining": rnd.defender_remaining,
        })

    return {
        "battle_id": req.battle_id,
        "status": result.status.value,
        "rounds": len(result.rounds),
        "attacker_losses": result.all_attacker_losses,
        "defender_losses": result.all_defender_losses,
        "territory_captured": result.territory_captured,
        "rng_seed": result.rng_seed,
        "state_version": new_version,
    }
