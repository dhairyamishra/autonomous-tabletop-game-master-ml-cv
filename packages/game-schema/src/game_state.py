"""Canonical game state schema for the WW2 Pacific 1940 2E referee system.

The official state is the single source of truth. CV observations never
directly mutate this state — all changes must pass through the rules engine.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from enums import (
    BattleStatus,
    ConfidenceBand,
    DiceMode,
    Phase,
    Player,
    UnitStatus,
    UnitType,
    VictoryStatus,
)


class Unit(BaseModel):
    unit_id: str = Field(default_factory=lambda: str(uuid4()))
    unit_type: UnitType
    owner: Player
    zone_id: str
    status: UnitStatus = UnitStatus.ACTIVE
    hits_taken: int = 0
    has_moved: bool = False
    has_attacked: bool = False
    carried_by: str | None = None    # transport unit_id if loaded
    carrying: list[str] = Field(default_factory=list)  # unit_ids of loaded units
    track_id: str | None = None      # CV tracker ID, not authoritative


class ZoneState(BaseModel):
    zone_id: str
    owner: Player | None = None      # None for uncaptured neutral / sea zones
    ipc_value: int = 0
    units: list[str] = Field(default_factory=list)  # unit_ids
    has_industrial_complex: bool = False
    industrial_complex_damage: int = 0
    is_capital: bool = False
    is_victory_city: bool = False


class Economy(BaseModel):
    treasury: dict[str, int] = Field(default_factory=dict)      # player -> IPC
    income: dict[str, int] = Field(default_factory=dict)        # player -> IPC per round
    pending_spend: dict[str, int] = Field(default_factory=dict) # player -> spent this purchase phase


class BattleParticipant(BaseModel):
    unit_id: str
    unit_type: UnitType
    owner: Player
    attack_value: int
    defense_value: int
    hits_taken: int = 0


class BattleRound(BaseModel):
    round_number: int
    attacker_rolls: list[int]
    defender_rolls: list[int]
    attacker_hits: int
    defender_hits: int
    attacker_casualties: list[str]   # unit_ids
    defender_casualties: list[str]   # unit_ids


class PendingBattle(BaseModel):
    battle_id: str = Field(default_factory=lambda: str(uuid4()))
    zone_id: str
    attacker: Player
    defender: Player
    attacking_units: list[str] = Field(default_factory=list)    # unit_ids
    defending_units: list[str] = Field(default_factory=list)    # unit_ids
    rounds: list[BattleRound] = Field(default_factory=list)
    status: BattleStatus = BattleStatus.PENDING
    rng_seed: str | None = None
    rng_algorithm: str | None = None
    battle_input_hash: str | None = None


class PendingPlacement(BaseModel):
    player: Player
    unit_type: UnitType
    count: int
    zone_id: str | None = None  # None until player chooses placement zone


class VisionReconciliationStatus(BaseModel):
    last_observation_id: str | None = None
    last_observation_at: datetime | None = None
    pending_confirmations: list[str] = Field(default_factory=list)
    confidence_band: ConfidenceBand = ConfidenceBand.HIGH
    has_unresolved_ambiguity: bool = False


class Audit(BaseModel):
    state_version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_by: str | None = None  # session_id or "system"
    checksum: str | None = None


class TurnState(BaseModel):
    round: int = 1
    current_player: Player = Player.JAPAN
    phase: Phase = Phase.SETUP
    phase_started_at: datetime = Field(default_factory=datetime.utcnow)


class GameState(BaseModel):
    """The authoritative game state. Only the rules engine may commit changes."""

    game_id: str = Field(default_factory=lambda: str(uuid4()))
    scenario: str = "ww2_pacific_1940_2nd_edition"
    ruleset_version: str = "1.0.0"
    dice_mode: DiceMode = DiceMode.NORMAL_SIMULATED

    players: list[Player] = Field(default_factory=lambda: list([
        Player.JAPAN, Player.USA, Player.UK_PACIFIC, Player.ANZAC, Player.CHINA
    ]))

    turn: TurnState = Field(default_factory=TurnState)
    economy: Economy = Field(default_factory=Economy)

    zones: dict[str, ZoneState] = Field(default_factory=dict)
    units: dict[str, Unit] = Field(default_factory=dict)

    pending_battles: dict[str, PendingBattle] = Field(default_factory=dict)
    pending_placements: list[PendingPlacement] = Field(default_factory=list)
    pending_actions: list[dict[str, Any]] = Field(default_factory=list)

    vision_reconciliation_status: VisionReconciliationStatus = Field(
        default_factory=VisionReconciliationStatus
    )
    victory_status: VictoryStatus = VictoryStatus.IN_PROGRESS
    winner: Player | None = None

    audit: Audit = Field(default_factory=Audit)

    def get_units_in_zone(self, zone_id: str) -> list[Unit]:
        return [u for u in self.units.values() if u.zone_id == zone_id]

    def get_player_units(self, player: Player) -> list[Unit]:
        return [u for u in self.units.values() if u.owner == player]

    def get_zone(self, zone_id: str) -> ZoneState | None:
        return self.zones.get(zone_id)
