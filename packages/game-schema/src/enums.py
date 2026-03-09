"""Shared enums for the WW2 Pacific 1940 2E referee system.

These are the canonical enum definitions used across all backend modules.
JSON Schema is generated from these for frontend TypeScript type generation.
"""
from enum import Enum


class Player(str, Enum):
    JAPAN = "japan"
    USA = "usa"
    UK_PACIFIC = "uk_pacific"
    ANZAC = "anzac"
    CHINA = "china"


class Phase(str, Enum):
    SETUP = "setup"
    PURCHASE = "purchase"
    COMBAT_MOVE = "combat_move"
    CONDUCT_COMBAT = "conduct_combat"
    NON_COMBAT_MOVE = "non_combat_move"
    MOBILIZE_NEW_UNITS = "mobilize_new_units"
    COLLECT_INCOME = "collect_income"
    TURN_END = "turn_end"


PHASE_ORDER = [
    Phase.PURCHASE,
    Phase.COMBAT_MOVE,
    Phase.CONDUCT_COMBAT,
    Phase.NON_COMBAT_MOVE,
    Phase.MOBILIZE_NEW_UNITS,
    Phase.COLLECT_INCOME,
    Phase.TURN_END,
]

PLAYER_ORDER = [
    Player.JAPAN,
    Player.USA,
    Player.UK_PACIFIC,
    Player.ANZAC,
    Player.CHINA,
]


class ZoneType(str, Enum):
    LAND = "land"
    SEA = "sea"


class UnitType(str, Enum):
    INFANTRY = "infantry"
    ARTILLERY = "artillery"
    ARMOR = "armor"
    FIGHTER = "fighter"
    BOMBER = "bomber"
    BATTLESHIP = "battleship"
    CARRIER = "carrier"
    CRUISER = "cruiser"
    DESTROYER = "destroyer"
    SUBMARINE = "submarine"
    TRANSPORT = "transport"
    INDUSTRIAL_COMPLEX = "industrial_complex"
    ANTIAIRCRAFT_GUN = "antiaircraft_gun"


class UnitStatus(str, Enum):
    ACTIVE = "active"
    DAMAGED = "damaged"      # Two-hit units (battleship) that have taken one hit
    MOBILIZING = "mobilizing"  # Purchased, not yet placed
    RETREATING = "retreating"
    SUNK = "sunk"
    DESTROYED = "destroyed"


class EventType(str, Enum):
    GAME_CREATED = "game_created"
    CALIBRATION_COMPLETED = "calibration_completed"
    OBSERVATION_RECEIVED = "observation_received"
    PROPOSED_STATE_GENERATED = "proposed_state_generated"
    MANUAL_CORRECTION_APPLIED = "manual_correction_applied"
    PURCHASE_COMMITTED = "purchase_committed"
    MOVE_COMMITTED = "move_committed"
    COMBAT_DECLARED = "combat_declared"
    BATTLE_STARTED = "battle_started"
    BATTLE_ROUND_ROLLED = "battle_round_rolled"
    CASUALTIES_ASSIGNED = "casualties_assigned"
    RETREAT_DECLARED = "retreat_declared"
    BATTLE_RESOLVED = "battle_resolved"
    PLACEMENT_COMMITTED = "placement_committed"
    INCOME_COLLECTED = "income_collected"
    PHASE_ADVANCED = "phase_advanced"
    TURN_ENDED = "turn_ended"
    GAME_ENDED = "game_ended"
    REFEREE_OVERRIDE = "referee_override"
    OBSERVATION_CORRECTION = "observation_correction"


class BattleStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ATTACKER_WON = "attacker_won"
    DEFENDER_WON = "defender_won"
    ATTACKER_RETREATED = "attacker_retreated"
    DRAWN = "drawn"


class CorrectionType(str, Enum):
    OBSERVATION_CORRECTION = "observation_correction"
    REFEREE_OVERRIDE = "referee_override"


class ConfidenceBand(str, Enum):
    HIGH = "high"       # >= 0.85
    MEDIUM = "medium"   # 0.60 – 0.85
    LOW = "low"         # 0.40 – 0.60
    VERY_LOW = "very_low"  # < 0.40


class DiceMode(str, Enum):
    NORMAL_SIMULATED = "normal_simulated"


class VictoryStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    JAPAN_WINS = "japan_wins"
    ALLIES_WIN = "allies_win"
