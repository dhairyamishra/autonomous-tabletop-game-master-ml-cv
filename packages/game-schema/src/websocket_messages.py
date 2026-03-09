"""WebSocket message schema for real-time server-to-client push events.

The backend pushes typed messages to all connected clients in a session.
Each message has a `type` discriminator, `timestamp`, and `session_id`.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from enums import Phase, Player


class BaseWsMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StateUpdatedMessage(BaseWsMessage):
    """Pushed after every official state commit."""
    type: Literal["state_updated"] = "state_updated"
    game_id: str
    state_version: int
    current_player: Player
    current_phase: Phase
    summary: dict[str, Any] = Field(default_factory=dict)  # lightweight diff hint


class ObservationFrameMessage(BaseWsMessage):
    """Pushed with each processed camera frame observation."""
    type: Literal["observation_frame"] = "observation_frame"
    game_id: str
    observation_id: str
    frame_id: int
    detection_count: int
    confidence_band: str
    requires_confirmation: bool
    flagged_zones: list[str] = Field(default_factory=list)


class BattleProgressMessage(BaseWsMessage):
    """Pushed for each battle round during combat resolution."""
    type: Literal["battle_progress"] = "battle_progress"
    game_id: str
    battle_id: str
    zone_id: str
    round_number: int
    attacker_rolls: list[int]
    defender_rolls: list[int]
    attacker_hits: int
    defender_hits: int
    attacker_remaining: int
    defender_remaining: int


class PhaseChangedMessage(BaseWsMessage):
    """Pushed when the active phase or player changes."""
    type: Literal["phase_changed"] = "phase_changed"
    game_id: str
    round: int
    player: Player
    phase: Phase
    state_version: int


class CorrectionRequestedMessage(BaseWsMessage):
    """Pushed when vision detects an ambiguity that needs operator confirmation."""
    type: Literal["correction_requested"] = "correction_requested"
    game_id: str
    observation_id: str
    flagged_zones: list[str]
    reasons: list[str]


class ErrorMessage(BaseWsMessage):
    """Pushed for server-side errors or validation failures."""
    type: Literal["error"] = "error"
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


# All outbound message types
AnyWsMessage = (
    StateUpdatedMessage
    | ObservationFrameMessage
    | BattleProgressMessage
    | PhaseChangedMessage
    | CorrectionRequestedMessage
    | ErrorMessage
)
