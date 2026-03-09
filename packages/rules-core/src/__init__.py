"""rules-core: pure game logic for WW2 Pacific 1940 2E. No I/O."""
from .economy import (
    PurchaseItem,
    PurchaseValidationResult,
    apply_territory_capture,
    china_production,
    collect_income,
    get_placement_capacity,
    validate_purchase,
)
from .map_data import (
    MapData,
    ZoneInfo,
    are_adjacent,
    get_attack_value,
    get_carrier_capacity,
    get_defense_value,
    get_ipc_value,
    get_map,
    get_movement_range,
    get_transport_capacity,
    get_unit_cost,
    get_zone_type,
    is_two_hit,
    land_zones_adjacent_to,
    load_map,
    reachable_zones,
    sea_zones_adjacent_to,
)
from .movement import (
    MoveRequest,
    ValidationResult,
    validate_move,
    validate_placement,
    validate_transport_load,
)
from .phase_machine import (
    PhaseTransitionResult,
    advance_phase,
    can_advance_phase,
    get_legal_phases_for_action,
    is_action_legal_in_phase,
)
from .setup import build_initial_state
from .victory import check_victory, count_victory_cities

__all__ = [
    "PurchaseItem", "PurchaseValidationResult", "apply_territory_capture",
    "china_production", "collect_income", "get_placement_capacity", "validate_purchase",
    "MapData", "ZoneInfo", "are_adjacent", "get_attack_value", "get_carrier_capacity",
    "get_defense_value", "get_ipc_value", "get_map", "get_movement_range",
    "get_transport_capacity", "get_unit_cost", "get_zone_type", "is_two_hit",
    "land_zones_adjacent_to", "load_map", "reachable_zones", "sea_zones_adjacent_to",
    "MoveRequest", "ValidationResult", "validate_move", "validate_placement",
    "validate_transport_load",
    "PhaseTransitionResult", "advance_phase", "can_advance_phase",
    "get_legal_phases_for_action", "is_action_legal_in_phase",
    "build_initial_state",
    "check_victory", "count_victory_cities",
]
