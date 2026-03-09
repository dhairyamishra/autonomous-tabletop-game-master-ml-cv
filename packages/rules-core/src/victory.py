"""Victory condition checks for WW2 Pacific 1940 2E.

Japan wins by controlling the required number of victory cities.
Allies win by preventing Japan from doing so.
Pure logic — no I/O.
"""
from __future__ import annotations

from game_schema.enums import Player, VictoryStatus
from game_schema.game_state import GameState

from .map_data import get_map


def check_victory(state: GameState) -> tuple[VictoryStatus, Player | None, str]:
    """Check victory conditions.

    Returns (status, winner_or_None, description).
    """
    md = get_map()
    vc_ids = md.victory_cities
    japan_threshold = md.japan_victory_threshold

    japan_vcs = sum(
        1 for vc in vc_ids
        if state.zones.get(vc) and state.zones[vc].owner == Player.JAPAN
    )

    if japan_vcs >= japan_threshold:
        return (
            VictoryStatus.JAPAN_WINS,
            Player.JAPAN,
            f"Japan controls {japan_vcs}/{japan_threshold} victory cities.",
        )

    # Check if Japan's capital is captured
    japan_capital = _find_capital(Player.JAPAN, state)
    if japan_capital:
        cap_state = state.zones.get(japan_capital)
        if cap_state and cap_state.owner != Player.JAPAN:
            return (
                VictoryStatus.ALLIES_WIN,
                None,  # collective Allied victory
                "Japan's capital has been captured.",
            )

    return VictoryStatus.IN_PROGRESS, None, ""


def count_victory_cities(state: GameState) -> dict[str, int]:
    """Return a count of victory cities held by each player."""
    md = get_map()
    counts: dict[str, int] = {p.value: 0 for p in Player}
    for vc in md.victory_cities:
        zone_state = state.zones.get(vc)
        if zone_state and zone_state.owner:
            counts[zone_state.owner.value] += 1
    return counts


def _find_capital(player: Player, state: GameState) -> str | None:
    md = get_map()
    for zone_id, zone_info in md.zones.items():
        if zone_info.is_capital and zone_info.default_owner == player:
            return zone_id
    return None
