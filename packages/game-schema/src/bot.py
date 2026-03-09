"""Bot suggestion schema for the WW2 Pacific 1940 2E advisor."""
from __future__ import annotations
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from enums import ConfidenceBand, Phase, Player, UnitType


class ActionItem(BaseModel):
    action_type: str    # "move", "attack", "purchase", "place", "retreat", "done"
    unit_id: str | None = None
    unit_type: UnitType | None = None
    from_zone: str | None = None
    to_zone: str | None = None
    count: int | None = None
    detail: str = ""


class ScoreBreakdown(BaseModel):
    territory_value: float = 0.0
    expected_enemy_value_destroyed: float = 0.0
    expected_own_value_lost: float = 0.0
    positional_gain: float = 0.0
    capital_safety: float = 0.0
    follow_up_mobility: float = 0.0
    counterattack_risk: float = 0.0
    total: float = 0.0


class SimulationSummary(BaseModel):
    simulations_run: int = 0
    win_probability: float = 0.0
    expected_attacker_losses: float = 0.0
    expected_defender_losses: float = 0.0
    ipc_swing: float = 0.0         # positive = attacker gain


class BotSuggestion(BaseModel):
    suggestion_id: str = Field(default_factory=lambda: str(uuid4()))
    rank: int                       # 1 = best
    player: Player
    phase: Phase
    actions: list[ActionItem]
    score: float
    score_breakdown: ScoreBreakdown
    reasoning: str                  # human-readable explanation
    confidence_band: ConfidenceBand
    simulation_summary: SimulationSummary | None = None
    warnings: list[str] = Field(default_factory=list)


class BotSuggestionResponse(BaseModel):
    game_id: str
    player: Player
    phase: Phase
    suggestions: list[BotSuggestion]   # top-k, ranked best first
    computation_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
