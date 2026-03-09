"""Legal move validation for WW2 Pacific 1940 2E.

Pure logic only — no database, no network.
Input: GameState + a proposed move
Output: (is_legal: bool, reason: str)
"""
from __future__ import annotations
from dataclasses import dataclass

from game_schema.enums import Phase, Player, UnitStatus, UnitType, ZoneType
from game_schema.game_state import GameState, Unit

from .map_data import (
    are_adjacent,
    get_map,
    get_movement_range,
    get_zone_type,
    reachable_zones,
)


@dataclass
class MoveRequest:
    unit_id: str
    to_zone: str
    load_unit_ids: list[str] | None = None   # units to load onto this transport
    unload_to_zone: str | None = None         # for transport unloading


@dataclass
class ValidationResult:
    is_legal: bool
    reason: str = ""


def validate_move(
    state: GameState,
    player: Player,
    phase: Phase,
    move: MoveRequest,
) -> ValidationResult:
    """Validate a unit move request against game rules."""
    unit = state.units.get(move.unit_id)
    if unit is None:
        return ValidationResult(False, f"Unit {move.unit_id} not found.")
    if unit.owner != player:
        return ValidationResult(False, f"Unit {move.unit_id} belongs to {unit.owner}, not {player}.")
    if unit.status not in (UnitStatus.ACTIVE, UnitStatus.DAMAGED):
        return ValidationResult(False, f"Unit {move.unit_id} is not in a movable state ({unit.status}).")
    if unit.has_moved:
        return ValidationResult(False, f"Unit {move.unit_id} has already moved this turn.")
    if unit.carried_by is not None:
        return ValidationResult(False, f"Unit {move.unit_id} is carried and cannot move independently.")

    from_zone = unit.zone_id
    to_zone = move.to_zone

    if from_zone == to_zone:
        return ValidationResult(False, "Unit is already in the destination zone.")

    dest_info = get_map().zones.get(to_zone)
    if dest_info is None:
        return ValidationResult(False, f"Destination zone {to_zone!r} does not exist.")

    unit_zone_type = get_zone_type(from_zone)
    dest_zone_type = dest_info.zone_type

    if unit.unit_type in (
        UnitType.INFANTRY, UnitType.ARTILLERY, UnitType.ARMOR,
        UnitType.INDUSTRIAL_COMPLEX, UnitType.ANTIAIRCRAFT_GUN,
    ):
        return _validate_land_unit_move(state, unit, from_zone, to_zone, phase)

    if unit.unit_type in (
        UnitType.FIGHTER, UnitType.BOMBER,
    ):
        return _validate_air_unit_move(state, unit, from_zone, to_zone, phase)

    if unit.unit_type in (
        UnitType.BATTLESHIP, UnitType.CARRIER, UnitType.CRUISER,
        UnitType.DESTROYER, UnitType.SUBMARINE, UnitType.TRANSPORT,
    ):
        return _validate_naval_unit_move(state, unit, from_zone, to_zone, phase, move)

    return ValidationResult(False, f"Unknown unit type {unit.unit_type}.")


def _validate_land_unit_move(
    state: GameState, unit: Unit, from_zone: str, to_zone: str, phase: Phase
) -> ValidationResult:
    md = get_map()
    dest = md.zones.get(to_zone)

    if dest is None or dest.zone_type != ZoneType.LAND:
        return ValidationResult(False, "Land units can only move to land territories.")

    mv_range = get_movement_range(unit.unit_type)

    # Check reachability through friendly/neutral land territories only
    reachable = _land_reachable_for_land_unit(state, unit.owner, from_zone, mv_range, phase)
    if to_zone not in reachable:
        return ValidationResult(False, f"Zone {to_zone!r} is not reachable in {mv_range} moves.")

    if phase == Phase.NON_COMBAT_MOVE:
        zone_state = state.zones.get(to_zone)
        if zone_state and zone_state.owner not in (unit.owner, None):
            if to_zone not in _captured_this_turn(state):
                return ValidationResult(False, "Non-combat move cannot enter enemy-controlled territory.")

    return ValidationResult(True)


def _land_reachable_for_land_unit(
    state: GameState, player: Player, start: str, mv_range: int,
    phase: Phase, visited: frozenset[str] | None = None,
) -> set[str]:
    """Land territories reachable from start, respecting combat-move / NCM rules."""
    if mv_range <= 0:
        return set()
    if visited is None:
        visited = frozenset()

    md = get_map()
    result: set[str] = set()
    info = md.zones.get(start)
    if not info:
        return result

    for neighbor in info.adjacent:
        if neighbor in visited:
            continue
        n_info = md.zones.get(neighbor)
        if not n_info or n_info.zone_type != ZoneType.LAND:
            continue
        n_zone_state = state.zones.get(neighbor)
        n_owner = n_zone_state.owner if n_zone_state else None

        if phase == Phase.NON_COMBAT_MOVE:
            if n_owner not in (player, None) and neighbor not in _captured_this_turn(state):
                continue  # cannot pass through enemy territory in NCM

        result.add(neighbor)
        deeper = _land_reachable_for_land_unit(
            state, player, neighbor, mv_range - 1, phase,
            visited=visited | {start},
        )
        result.update(deeper)

    return result


def _captured_this_turn(state: GameState) -> set[str]:
    """Return zone_ids captured during the current combat phase (placeholder)."""
    return set()


def _validate_air_unit_move(
    state: GameState, unit: Unit, from_zone: str, to_zone: str, phase: Phase
) -> ValidationResult:
    mv_range = get_movement_range(unit.unit_type)
    reachable = reachable_zones(from_zone, mv_range)
    if to_zone not in reachable:
        return ValidationResult(False, f"Air unit cannot reach {to_zone!r} in {mv_range} moves.")

    # Air units must be able to land somewhere friendly
    if not _can_air_land(state, unit, to_zone):
        return ValidationResult(False, f"No valid landing spot for air unit at {to_zone!r}.")

    return ValidationResult(True)


def _can_air_land(state: GameState, unit: Unit, zone_id: str) -> bool:
    """Check that an air unit can land at zone_id (friendly territory or carrier)."""
    zone_info = get_map().zones.get(zone_id)
    if zone_info is None:
        return False

    # Friendly land territory
    if zone_info.zone_type == ZoneType.LAND:
        zone_state = state.zones.get(zone_id)
        return zone_state is not None and zone_state.owner == unit.owner

    # Sea zone — check for a friendly carrier with available deck space
    if zone_info.zone_type == ZoneType.SEA:
        carrier_units = [
            u for u in state.units.values()
            if u.zone_id == zone_id
            and u.owner == unit.owner
            and u.unit_type == UnitType.CARRIER
            and u.status != UnitStatus.SUNK
        ]
        for carrier in carrier_units:
            current_fighters = len([
                u for u in state.units.values()
                if u.carried_by == carrier.unit_id
            ])
            if current_fighters < 2:  # carrier capacity = 2
                return True

    return False


def _validate_naval_unit_move(
    state: GameState, unit: Unit, from_zone: str, to_zone: str, phase: Phase,
    move: MoveRequest,
) -> ValidationResult:
    dest = get_map().zones.get(to_zone)
    if dest is None or dest.zone_type != ZoneType.SEA:
        if unit.unit_type == UnitType.TRANSPORT and move.unload_to_zone:
            return ValidationResult(True)  # transport delivering to adjacent land
        return ValidationResult(False, "Naval units can only move to sea zones.")

    mv_range = get_movement_range(unit.unit_type)
    reachable = reachable_zones(from_zone, mv_range, sea_only=True)
    if to_zone not in reachable:
        return ValidationResult(False, f"Naval unit cannot reach {to_zone!r} in {mv_range} moves.")

    if unit.unit_type == UnitType.TRANSPORT:
        if phase == Phase.COMBAT_MOVE:
            return ValidationResult(False, "Transports cannot participate in combat moves.")

    return ValidationResult(True)


def validate_transport_load(
    state: GameState, transport_id: str, unit_ids: list[str],
) -> ValidationResult:
    """Validate loading units onto a transport."""
    transport = state.units.get(transport_id)
    if transport is None or transport.unit_type != UnitType.TRANSPORT:
        return ValidationResult(False, "Not a valid transport.")

    current_load = len(transport.carrying)
    capacity = 2  # standard transport capacity
    if current_load + len(unit_ids) > capacity:
        return ValidationResult(False, f"Transport capacity exceeded ({capacity}).")

    for uid in unit_ids:
        unit = state.units.get(uid)
        if unit is None:
            return ValidationResult(False, f"Unit {uid} not found.")
        if unit.unit_type not in (UnitType.INFANTRY, UnitType.ARTILLERY, UnitType.ARMOR):
            return ValidationResult(False, f"Unit type {unit.unit_type} cannot be transported.")
        if unit.zone_id != transport.zone_id and not are_adjacent(unit.zone_id, transport.zone_id):
            return ValidationResult(False, "Unit is not adjacent to transport for loading.")

    return ValidationResult(True)


def validate_placement(
    state: GameState, player: Player, unit_type: UnitType, zone_id: str,
) -> ValidationResult:
    """Validate placing a newly purchased unit."""
    from game_schema.enums import ZoneType as ZT
    md = get_map()
    zone_info = md.zones.get(zone_id)
    if zone_info is None:
        return ValidationResult(False, f"Zone {zone_id!r} does not exist.")

    zone_state = state.zones.get(zone_id)
    if zone_state is None or zone_state.owner != player:
        return ValidationResult(False, "Can only place units in controlled territories.")

    is_land_unit = unit_type in (
        UnitType.INFANTRY, UnitType.ARTILLERY, UnitType.ARMOR,
        UnitType.ANTIAIRCRAFT_GUN,
    )
    is_naval = unit_type in (
        UnitType.BATTLESHIP, UnitType.CARRIER, UnitType.CRUISER,
        UnitType.DESTROYER, UnitType.SUBMARINE, UnitType.TRANSPORT,
    )

    if zone_info.zone_type == ZoneType.LAND:
        if not zone_state.has_industrial_complex:
            return ValidationResult(False, "No industrial complex in this territory.")

        # Production limit: territory IPC value
        placed_this_turn = sum(
            1 for u in state.units.values()
            if u.owner == player and u.zone_id == zone_id and u.status == UnitStatus.MOBILIZING
        )
        prod_limit = zone_state.ipc_value
        if placed_this_turn >= prod_limit:
            return ValidationResult(
                False, f"Production limit of {prod_limit} reached for {zone_id}."
            )

        if is_naval:
            # Naval units go in an adjacent sea zone — redirect to a sea-zone validation
            return ValidationResult(False, "Naval units must be placed in an adjacent sea zone.")

        return ValidationResult(True)

    if zone_info.zone_type == ZoneType.SEA:
        if not is_naval:
            return ValidationResult(False, "Land units cannot be placed in sea zones.")
        # Must be adjacent to a friendly IC territory
        adj_ics = [
            z for z in zone_info.adjacent
            if md.zones.get(z) and md.zones[z].zone_type == ZoneType.LAND
            and state.zones.get(z)
            and state.zones[z].has_industrial_complex
            and state.zones[z].owner == player
        ]
        if not adj_ics:
            return ValidationResult(False, "No adjacent friendly industrial complex.")
        return ValidationResult(True)

    return ValidationResult(False, "Unknown zone type.")
