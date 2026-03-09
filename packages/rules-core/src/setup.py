"""Game initialization — loads the canonical starting state from map data.

Produces the first authoritative GameState for a new game.
Pure logic — no I/O (map data is loaded by map_data module).
"""
from __future__ import annotations
from uuid import uuid4

from game_schema.enums import Phase, Player, UnitStatus, UnitType
from game_schema.game_state import (
    Economy,
    GameState,
    TurnState,
    Unit,
    ZoneState,
)

from .map_data import get_map


def build_initial_state(game_id: str | None = None) -> GameState:
    """Create the canonical starting GameState for WW2 Pacific 1940 2E."""
    md = get_map()
    game_id = game_id or str(uuid4())

    # Build zones
    zones: dict[str, ZoneState] = {}
    for zone_id, zone_info in md.zones.items():
        zones[zone_id] = ZoneState(
            zone_id=zone_id,
            owner=zone_info.default_owner,
            ipc_value=zone_info.ipc,
            units=[],
            has_industrial_complex=zone_info.has_industrial_complex,
            industrial_complex_damage=0,
            is_capital=zone_info.is_capital,
            is_victory_city=zone_info.is_victory_city,
        )

    # Build units from starting placements
    units: dict[str, Unit] = {}
    for player_str, player_zones in md.starting_units.items():
        player = Player(player_str)
        for zone_id, unit_counts in player_zones.items():
            for unit_type_str, count in unit_counts.items():
                unit_type = UnitType(unit_type_str)
                for _ in range(count):
                    uid = str(uuid4())
                    units[uid] = Unit(
                        unit_id=uid,
                        unit_type=unit_type,
                        owner=player,
                        zone_id=zone_id,
                        status=UnitStatus.ACTIVE,
                    )
                    zones[zone_id].units.append(uid)

    # Build economy
    economy = Economy(
        treasury={p.value: md.starting_ipc.get(p.value, 0) for p in Player},
        income={p.value: 0 for p in Player},
        pending_spend={p.value: 0 for p in Player},
    )

    state = GameState(
        game_id=game_id,
        turn=TurnState(round=1, current_player=Player.JAPAN, phase=Phase.SETUP),
        economy=economy,
        zones=zones,
        units=units,
    )

    return state
