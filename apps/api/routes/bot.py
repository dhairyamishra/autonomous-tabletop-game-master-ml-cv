"""Bot suggestion endpoint."""
from __future__ import annotations
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from game_schema.enums import Phase, Player
from ..state_store import get_store

router = APIRouter(prefix="/bot", tags=["Bot"])


class BotSuggestRequest(BaseModel):
    game_id: str
    player: str
    phase: str


@router.post("/suggest")
async def bot_suggest(req: BotSuggestRequest) -> dict[str, Any]:
    """Get bot suggestions for the given player/phase."""
    store = get_store()
    state = await store.get(req.game_id)
    if state is None:
        raise HTTPException(404, "Game not found.")

    player = Player(req.player)
    phase = Phase(req.phase)

    # Import bot module lazily
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))
    from modules.bot.advisor import get_suggestions

    suggestions = get_suggestions(state, player, phase)
    return {
        "game_id": req.game_id,
        "player": player.value,
        "phase": phase.value,
        "suggestions": [s.model_dump() for s in suggestions],
    }
