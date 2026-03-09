"""Map data loader and graph utilities for WW2 Pacific 1940 2E.

Loads the canonical map JSON and provides adjacency lookups,
IPC queries, and zone-type helpers. No I/O at call time — data
is loaded once at import and cached.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from game_schema.enums import Player, UnitType, ZoneType

_MAP_JSON_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "map" / "pacific_1940_2e.json"
)


@dataclass(frozen=True)
class ZoneInfo:
    zone_id: str
    zone_type: ZoneType
    ipc: int
    default_owner: Player | None
    is_capital: bool
    is_victory_city: bool
    has_industrial_complex: bool
    adjacent: frozenset[str]  # zone_ids (territories + sea zones)


@dataclass
class MapData:
    zones: dict[str, ZoneInfo] = field(default_factory=dict)
    unit_costs: dict[str, int] = field(default_factory=dict)
    unit_combat_values: dict[str, dict[str, Any]] = field(default_factory=dict)
    starting_units: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)
    starting_ipc: dict[str, int] = field(default_factory=dict)
    victory_cities: list[str] = field(default_factory=list)
    japan_victory_threshold: int = 6
    neutral_territories: list[str] = field(default_factory=list)
    special_rules: dict[str, Any] = field(default_factory=dict)
    canal_rules: dict[str, Any] = field(default_factory=dict)


def _player_or_none(raw: str | None) -> Player | None:
    if not raw:
        return None
    try:
        return Player(raw)
    except ValueError:
        return None


def load_map(path: Path | None = None) -> MapData:
    """Load and parse the map JSON into a MapData object."""
    path = path or _MAP_JSON_PATH
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    md = MapData(
        unit_costs=raw["unit_costs"],
        unit_combat_values=raw["unit_combat_values"],
        starting_units={
            player: {
                zone: counts
                for zone, counts in zones.items()
            }
            for player, zones in raw["starting_units"].items()
        },
        starting_ipc={k: v for k, v in raw["starting_ipc"].items()},
        victory_cities=raw["victory_cities"],
        japan_victory_threshold=raw["japan_victory_threshold"],
        neutral_territories=raw.get("neutral_territories", []),
        special_rules=raw.get("special_rules", {}),
        canal_rules=raw.get("canal_rules", {}),
    )

    for tid, tdata in raw["territories"].items():
        adj = frozenset(tdata.get("adjacent_territories", []))
        md.zones[tid] = ZoneInfo(
            zone_id=tid,
            zone_type=ZoneType.LAND,
            ipc=tdata.get("ipc", 0),
            default_owner=_player_or_none(tdata.get("owner")),
            is_capital=tdata.get("is_capital", False),
            is_victory_city=tdata.get("is_victory_city", False),
            has_industrial_complex=tdata.get("has_industrial_complex", False),
            adjacent=adj,
        )

    for szid, szdata in raw["sea_zones"].items():
        adj = frozenset(
            szdata.get("adjacent_territories", [])
            + szdata.get("adjacent_sea_zones", [])
        )
        md.zones[szid] = ZoneInfo(
            zone_id=szid,
            zone_type=ZoneType.SEA,
            ipc=0,
            default_owner=None,
            is_capital=False,
            is_victory_city=False,
            has_industrial_complex=False,
            adjacent=adj,
        )

    return md


_cached: MapData | None = None


def get_map() -> MapData:
    """Return the cached MapData singleton."""
    global _cached
    if _cached is None:
        _cached = load_map()
    return _cached


def are_adjacent(zone_a: str, zone_b: str) -> bool:
    md = get_map()
    info = md.zones.get(zone_a)
    return bool(info and zone_b in info.adjacent)


def get_zone_type(zone_id: str) -> ZoneType | None:
    info = get_map().zones.get(zone_id)
    return info.zone_type if info else None


def get_ipc_value(zone_id: str) -> int:
    info = get_map().zones.get(zone_id)
    return info.ipc if info else 0


def get_unit_cost(unit_type: UnitType) -> int:
    return get_map().unit_costs.get(unit_type.value, 0)


def get_movement_range(unit_type: UnitType) -> int:
    cv = get_map().unit_combat_values.get(unit_type.value, {})
    return cv.get("movement", 1)


def get_attack_value(unit_type: UnitType) -> int:
    cv = get_map().unit_combat_values.get(unit_type.value, {})
    return cv.get("attack", 0)


def get_defense_value(unit_type: UnitType) -> int:
    cv = get_map().unit_combat_values.get(unit_type.value, {})
    return cv.get("defense", 0)


def is_two_hit(unit_type: UnitType) -> bool:
    cv = get_map().unit_combat_values.get(unit_type.value, {})
    return cv.get("is_two_hit", False)


def get_carrier_capacity(unit_type: UnitType) -> int:
    cv = get_map().unit_combat_values.get(unit_type.value, {})
    return cv.get("capacity", 0)


def get_transport_capacity(unit_type: UnitType) -> int:
    cv = get_map().unit_combat_values.get(unit_type.value, {})
    return cv.get("capacity", 0)


def land_zones_adjacent_to(zone_id: str) -> list[str]:
    md = get_map()
    info = md.zones.get(zone_id)
    if not info:
        return []
    return [z for z in info.adjacent if md.zones.get(z, None) and md.zones[z].zone_type == ZoneType.LAND]


def sea_zones_adjacent_to(zone_id: str) -> list[str]:
    md = get_map()
    info = md.zones.get(zone_id)
    if not info:
        return []
    return [z for z in info.adjacent if md.zones.get(z, None) and md.zones[z].zone_type == ZoneType.SEA]


def reachable_zones(
    start_zone: str,
    movement_range: int,
    land_only: bool = False,
    sea_only: bool = False,
    visited: frozenset[str] | None = None,
) -> set[str]:
    """BFS over the adjacency graph up to movement_range steps."""
    if movement_range <= 0:
        return set()
    md = get_map()
    if visited is None:
        visited = frozenset()

    result: set[str] = set()
    info = md.zones.get(start_zone)
    if not info:
        return result

    for neighbor in info.adjacent:
        if neighbor in visited:
            continue
        n_info = md.zones.get(neighbor)
        if not n_info:
            continue
        if land_only and n_info.zone_type != ZoneType.LAND:
            continue
        if sea_only and n_info.zone_type != ZoneType.SEA:
            continue
        result.add(neighbor)
        if movement_range > 1:
            deeper = reachable_zones(
                neighbor,
                movement_range - 1,
                land_only=land_only,
                sea_only=sea_only,
                visited=visited | {start_zone},
            )
            result.update(deeper)
    return result
