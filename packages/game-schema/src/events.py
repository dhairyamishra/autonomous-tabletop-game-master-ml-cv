"""Event schema for the WW2 Pacific 1940 2E referee system.

Every meaningful state change is backed by a typed event stored in the event log.
The event log is the authoritative record for replay and audit.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from enums import (
    BattleStatus,
    CorrectionType,
    EventType,
    Phase,
    Player,
    UnitType,
)


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    game_id: str
    session_id: str
    actor: str          # session_id or "system"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state_version_before: int
    state_version_after: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class GameCreatedEvent(BaseEvent):
    event_type: EventType = EventType.GAME_CREATED
    scenario: str
    players: list[Player]
    dice_mode: str


class CalibrationCompletedEvent(BaseEvent):
    event_type: EventType = EventType.CALIBRATION_COMPLETED
    camera_id: str
    homography_matrix: list[list[float]]
    board_corners: list[list[float]]   # 4 corners in image coordinates


class ObservationReceivedEvent(BaseEvent):
    event_type: EventType = EventType.OBSERVATION_RECEIVED
    observation_id: str
    frame_id: int
    detection_count: int
    confidence_band: str


class ProposedStateGeneratedEvent(BaseEvent):
    event_type: EventType = EventType.PROPOSED_STATE_GENERATED
    observation_id: str
    delta_zone_ids: list[str]
    ambiguity_count: int
    requires_confirmation: bool


class ManualCorrectionAppliedEvent(BaseEvent):
    event_type: EventType = EventType.MANUAL_CORRECTION_APPLIED
    correction_type: CorrectionType
    zone_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    reason: str


class RefereeOverrideEvent(BaseEvent):
    event_type: EventType = EventType.REFEREE_OVERRIDE
    zone_id: str | None
    before_snapshot: dict[str, Any]
    after_snapshot: dict[str, Any]
    reason: str


class PurchaseCommittedEvent(BaseEvent):
    event_type: EventType = EventType.PURCHASE_COMMITTED
    player: Player
    purchases: list[dict[str, Any]]  # [{unit_type, count, cost}]
    total_cost: int
    treasury_before: int
    treasury_after: int


class MoveCommittedEvent(BaseEvent):
    event_type: EventType = EventType.MOVE_COMMITTED
    player: Player
    phase: Phase
    unit_id: str
    from_zone: str
    to_zone: str
    loaded_units: list[str] = Field(default_factory=list)  # for transports


class CombatDeclaredEvent(BaseEvent):
    event_type: EventType = EventType.COMBAT_DECLARED
    player: Player
    battles: list[dict[str, Any]]    # [{zone_id, attacking_units, defending_units}]


class BattleStartedEvent(BaseEvent):
    event_type: EventType = EventType.BATTLE_STARTED
    battle_id: str
    zone_id: str
    attacker: Player
    defender: Player
    attacking_units: list[dict[str, Any]]
    defending_units: list[dict[str, Any]]
    rng_seed: str
    rng_algorithm: str
    battle_input_hash: str


class BattleRoundRolledEvent(BaseEvent):
    event_type: EventType = EventType.BATTLE_ROUND_ROLLED
    battle_id: str
    round_number: int
    attacker_rolls: list[int]
    defender_rolls: list[int]
    attacker_hits: int
    defender_hits: int


class CasualtiesAssignedEvent(BaseEvent):
    event_type: EventType = EventType.CASUALTIES_ASSIGNED
    battle_id: str
    round_number: int
    attacker_casualties: list[str]   # unit_ids
    defender_casualties: list[str]   # unit_ids


class RetreatDeclaredEvent(BaseEvent):
    event_type: EventType = EventType.RETREAT_DECLARED
    battle_id: str
    retreating_player: Player
    retreat_to_zone: str
    retreating_units: list[str]  # unit_ids


class BattleResolvedEvent(BaseEvent):
    event_type: EventType = EventType.BATTLE_RESOLVED
    battle_id: str
    zone_id: str
    status: BattleStatus
    attacker: Player
    defender: Player
    total_rounds: int
    attacker_losses: list[str]   # unit_ids
    defender_losses: list[str]   # unit_ids
    territory_captured: bool


class PlacementCommittedEvent(BaseEvent):
    event_type: EventType = EventType.PLACEMENT_COMMITTED
    player: Player
    placements: list[dict[str, Any]]  # [{unit_type, count, zone_id}]


class IncomeCollectedEvent(BaseEvent):
    event_type: EventType = EventType.INCOME_COLLECTED
    player: Player
    territories_controlled: list[str]
    ipc_collected: int
    treasury_before: int
    treasury_after: int


class PhaseAdvancedEvent(BaseEvent):
    event_type: EventType = EventType.PHASE_ADVANCED
    player: Player
    from_phase: Phase
    to_phase: Phase


class TurnEndedEvent(BaseEvent):
    event_type: EventType = EventType.TURN_ENDED
    player: Player
    round: int
    next_player: Player


class GameEndedEvent(BaseEvent):
    event_type: EventType = EventType.GAME_ENDED
    winner: Player
    victory_condition: str
    final_round: int


# Union type for event deserialization
AnyEvent = (
    GameCreatedEvent
    | CalibrationCompletedEvent
    | ObservationReceivedEvent
    | ProposedStateGeneratedEvent
    | ManualCorrectionAppliedEvent
    | RefereeOverrideEvent
    | PurchaseCommittedEvent
    | MoveCommittedEvent
    | CombatDeclaredEvent
    | BattleStartedEvent
    | BattleRoundRolledEvent
    | CasualtiesAssignedEvent
    | RetreatDeclaredEvent
    | BattleResolvedEvent
    | PlacementCommittedEvent
    | IncomeCollectedEvent
    | PhaseAdvancedEvent
    | TurnEndedEvent
    | GameEndedEvent
)
