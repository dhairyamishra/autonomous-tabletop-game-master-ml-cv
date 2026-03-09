"""Economy logic for WW2 Pacific 1940 2E.

Handles IPC collection, purchase validation, territory capture effects.
Pure logic only — no I/O.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass

from game_schema.enums import Player, UnitType
from game_schema.game_state import GameState

from .map_data import get_map, get_unit_cost


@dataclass
class PurchaseItem:
    unit_type: UnitType
    count: int

    @property
    def cost(self) -> int:
        return get_unit_cost(self.unit_type) * self.count


@dataclass
class PurchaseValidationResult:
    is_legal: bool
    reason: str = ""
    total_cost: int = 0


def validate_purchase(
    state: GameState, player: Player, purchases: list[PurchaseItem],
) -> PurchaseValidationResult:
    """Check that a purchase list is within the player's budget."""
    treasury = state.economy.treasury.get(player.value, 0)
    total_cost = sum(p.cost for p in purchases)

    if total_cost > treasury:
        return PurchaseValidationResult(
            False,
            f"Purchase costs {total_cost} IPC but {player} only has {treasury} IPC.",
            total_cost,
        )

    # China cannot purchase anything; the system handles China production separately
    from game_schema.enums import Player as P
    if player == P.CHINA:
        return PurchaseValidationResult(
            False, "China uses special production rules; purchases are handled automatically."
        )

    return PurchaseValidationResult(True, total_cost=total_cost)


def collect_income(state: GameState, player: Player) -> tuple[int, list[str]]:
    """Calculate income for a player based on controlled territories.

    Returns (ipc_amount, controlled_territory_ids).
    Does NOT mutate state — caller applies the result.
    """
    capital_zone = _get_capital(player, state)
    if capital_zone:
        cap_state = state.zones.get(capital_zone)
        if cap_state and cap_state.owner != player:
            return 0, []  # capital is occupied; no income

    controlled: list[str] = []
    total_ipc = 0
    md = get_map()

    for zone_id, zone_state in state.zones.items():
        if zone_state.owner != player:
            continue
        zone_info = md.zones.get(zone_id)
        if zone_info and zone_info.ipc > 0:
            controlled.append(zone_id)
            total_ipc += zone_info.ipc

    return total_ipc, controlled


def _get_capital(player: Player, state: GameState) -> str | None:
    """Return zone_id of the player's capital."""
    md = get_map()
    for zone_id, zone_info in md.zones.items():
        if zone_info.is_capital and zone_info.default_owner == player:
            return zone_id
    return None


def get_placement_capacity(state: GameState, player: Player, zone_id: str) -> int:
    """Return how many units the player can still place in zone_id this turn."""
    zone_state = state.zones.get(zone_id)
    if not zone_state or not zone_state.has_industrial_complex:
        return 0
    if zone_state.owner != player:
        return 0

    # Production limit = IPC value of the territory (minus damage)
    zone_info = get_map().zones.get(zone_id)
    base_capacity = zone_info.ipc if zone_info else 0
    damage = zone_state.industrial_complex_damage
    capacity = max(0, base_capacity - damage)

    # Count already-mobilizing units in this zone
    from game_schema.enums import UnitStatus as US
    placed = sum(
        1 for u in state.units.values()
        if u.owner == player and u.zone_id == zone_id
        and u.status == US.MOBILIZING
    )
    return max(0, capacity - placed)


def apply_territory_capture(
    state: GameState, zone_id: str, new_owner: Player,
) -> GameState:
    """Return a new GameState with the territory captured by new_owner.

    Does NOT run combat — call after combat is resolved.
    """
    new_state = state.model_copy(deep=True)
    zone = new_state.zones.get(zone_id)
    if zone is None:
        return new_state

    old_owner = zone.owner
    zone.owner = new_owner
    new_state.zones[zone_id] = zone

    # Transfer any enemy land units that were not removed during combat
    # (should be empty after combat, but defensive guard)
    for unit in new_state.units.values():
        if unit.zone_id == zone_id and unit.owner == old_owner:
            pass  # combat should have cleared them; leave for caller to handle

    return new_state


def china_production(state: GameState) -> int:
    """China produces infantry equal to 1 per 3 territories it controls, max 6."""
    china_count = sum(
        1 for zid, zs in state.zones.items()
        if zs.owner == Player.CHINA
    )
    return min(6, china_count // 3)
