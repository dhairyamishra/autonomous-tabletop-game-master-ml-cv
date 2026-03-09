"""Simple heuristic bot advisor for WW2 Pacific 1940 2E.

Provides ranked suggestions for each game phase. Uses the same battle
simulator as the referee to evaluate attack options. Returns top-3 bundles.
"""
from __future__ import annotations
import sys, os, types
from typing import Any
from uuid import uuid4

# Ensure packages are importable when called without the API's path_setup
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
for _src in [
    os.path.join(_ROOT, "packages", "game-schema", "src"),
    os.path.join(_ROOT, "packages", "rules-core",  "src"),
    os.path.join(_ROOT, "packages", "battle-core",  "src"),
]:
    if _src not in sys.path:
        sys.path.insert(0, _src)

def _alias(name: str, path: str) -> None:
    if name not in sys.modules:
        pkg = types.ModuleType(name)
        pkg.__path__ = [path]
        pkg.__package__ = name
        sys.modules[name] = pkg

_alias("game_schema", os.path.join(_ROOT, "packages", "game-schema", "src"))
_alias("rules_core",  os.path.join(_ROOT, "packages", "rules-core",  "src"))
_alias("battle_core", os.path.join(_ROOT, "packages", "battle-core",  "src"))

from game_schema.bot import ActionItem, BotSuggestion, BotSuggestionResponse, ScoreBreakdown, SimulationSummary
from game_schema.enums import ConfidenceBand, Phase, Player, UnitType
from game_schema.game_state import GameState


def get_suggestions(
    state: GameState,
    player: Player,
    phase: Phase,
    top_k: int = 3,
) -> list[BotSuggestion]:
    """Route to the appropriate phase advisor and return top-k suggestions."""
    if phase == Phase.PURCHASE:
        return _purchase_advisor(state, player, top_k)
    if phase == Phase.COMBAT_MOVE:
        return _combat_move_advisor(state, player, top_k)
    if phase == Phase.CONDUCT_COMBAT:
        return _combat_decision_advisor(state, player, top_k)
    if phase == Phase.NON_COMBAT_MOVE:
        return _non_combat_advisor(state, player, top_k)
    if phase == Phase.MOBILIZE_NEW_UNITS:
        return _placement_advisor(state, player, top_k)
    return [_pass_suggestion(player, phase)]


# ── Purchase Advisor ──────────────────────────────────────────────────────────

def _purchase_advisor(state: GameState, player: Player, top_k: int) -> list[BotSuggestion]:
    treasury = state.economy.treasury.get(player.value, 0)
    if treasury == 0:
        return [_pass_suggestion(player, Phase.PURCHASE, "No IPC to spend.")]

    from rules_core.map_data import get_map
    md = get_map()
    costs = md.unit_costs

    suggestions: list[BotSuggestion] = []

    # Option 1: Infantry-heavy (defensive economy)
    inf_count = treasury // costs.get("infantry", 3)
    if inf_count > 0:
        actions = [ActionItem(action_type="purchase", unit_type=UnitType.INFANTRY, count=inf_count, detail=f"Cost: {inf_count * costs.get('infantry', 3)} IPC")]
        suggestions.append(BotSuggestion(
            suggestion_id=str(uuid4()),
            rank=1,
            player=player,
            phase=Phase.PURCHASE,
            actions=actions,
            score=_economy_score(state, player) + inf_count * 0.5,
            score_breakdown=ScoreBreakdown(territory_value=2.0, total=3.0),
            reasoning=f"Buy {inf_count} infantry to fill territories. Cheapest defensive option.",
            confidence_band=ConfidenceBand.HIGH,
        ))

    # Option 2: Mixed balanced purchase
    remaining = treasury
    mixed_actions: list[ActionItem] = []
    if remaining >= costs.get("fighter", 10):
        mixed_actions.append(ActionItem(action_type="purchase", unit_type=UnitType.FIGHTER, count=1))
        remaining -= costs.get("fighter", 10)
    if remaining >= costs.get("infantry", 3):
        n = remaining // costs.get("infantry", 3)
        mixed_actions.append(ActionItem(action_type="purchase", unit_type=UnitType.INFANTRY, count=n))
        remaining -= n * costs.get("infantry", 3)
    if mixed_actions:
        suggestions.append(BotSuggestion(
            suggestion_id=str(uuid4()),
            rank=2,
            player=player,
            phase=Phase.PURCHASE,
            actions=mixed_actions,
            score=_economy_score(state, player) + 2.0,
            score_breakdown=ScoreBreakdown(positional_gain=1.5, total=3.5),
            reasoning="Balanced: one fighter for air power, remaining budget on infantry.",
            confidence_band=ConfidenceBand.MEDIUM,
        ))

    # Option 3: Naval investment (if coastal IC exists)
    has_coastal_ic = _has_coastal_industrial_complex(state, player)
    if has_coastal_ic and treasury >= costs.get("destroyer", 8):
        naval_actions = [ActionItem(action_type="purchase", unit_type=UnitType.DESTROYER, count=1, detail="Sea control")]
        if treasury - costs.get("destroyer", 8) >= costs.get("infantry", 3):
            n = (treasury - costs.get("destroyer", 8)) // costs.get("infantry", 3)
            naval_actions.append(ActionItem(action_type="purchase", unit_type=UnitType.INFANTRY, count=n))
        suggestions.append(BotSuggestion(
            suggestion_id=str(uuid4()),
            rank=3,
            player=player,
            phase=Phase.PURCHASE,
            actions=naval_actions,
            score=_economy_score(state, player) + 1.5,
            score_breakdown=ScoreBreakdown(follow_up_mobility=2.0, total=3.5),
            reasoning="Invest in sea control with a destroyer, then fill remaining budget with infantry.",
            confidence_band=ConfidenceBand.MEDIUM,
        ))

    return sorted(suggestions, key=lambda s: -s.score)[:top_k]


# ── Combat Move Advisor ───────────────────────────────────────────────────────

def _combat_move_advisor(state: GameState, player: Player, top_k: int) -> list[BotSuggestion]:
    from rules_core.map_data import get_map
    md = get_map()

    player_units = [u for u in state.units.values() if u.owner == player and not u.has_moved]
    attack_options: list[dict[str, Any]] = []

    # Find enemy territories adjacent to our units
    for unit in player_units:
        zone_info = md.zones.get(unit.zone_id)
        if not zone_info:
            continue
        for adj_id in zone_info.adjacent:
            adj_zone = state.zones.get(adj_id)
            if adj_zone and adj_zone.owner and adj_zone.owner != player:
                # Enemy-held adjacent territory
                enemy_units = [u for u in state.units.values() if u.zone_id == adj_id]
                ipc_gain = adj_zone.ipc_value
                attack_options.append({
                    "unit_id": unit.unit_id,
                    "from_zone": unit.zone_id,
                    "to_zone": adj_id,
                    "enemy_count": len(enemy_units),
                    "ipc_gain": ipc_gain,
                })

    if not attack_options:
        return [_pass_suggestion(player, Phase.COMBAT_MOVE, "No adjacent enemy territories.")]

    # Score attacks by IPC gain vs enemy strength
    scored = sorted(
        attack_options,
        key=lambda a: a["ipc_gain"] - a["enemy_count"] * 0.5,
        reverse=True,
    )

    suggestions: list[BotSuggestion] = []
    for i, opt in enumerate(scored[:top_k]):
        suggestions.append(BotSuggestion(
            suggestion_id=str(uuid4()),
            rank=i + 1,
            player=player,
            phase=Phase.COMBAT_MOVE,
            actions=[ActionItem(
                action_type="move",
                unit_id=opt["unit_id"],
                from_zone=opt["from_zone"],
                to_zone=opt["to_zone"],
                detail=f"Attack — {opt['ipc_gain']} IPC at stake, {opt['enemy_count']} defenders",
            )],
            score=float(opt["ipc_gain"] - opt["enemy_count"] * 0.3),
            score_breakdown=ScoreBreakdown(
                territory_value=float(opt["ipc_gain"]),
                counterattack_risk=float(opt["enemy_count"] * 0.3),
                total=float(opt["ipc_gain"] - opt["enemy_count"] * 0.3),
            ),
            reasoning=f"Move to {opt['to_zone'].replace('_', ' ')} ({opt['ipc_gain']} IPC). {opt['enemy_count']} enemy units defending.",
            confidence_band=ConfidenceBand.MEDIUM,
        ))
    return suggestions


# ── Combat Decision Advisor ───────────────────────────────────────────────────

def _combat_decision_advisor(state: GameState, player: Player, top_k: int) -> list[BotSuggestion]:
    pending = [b for b in state.pending_battles.values() if b.attacker == player and b.status.value == "pending"]
    if not pending:
        return [_pass_suggestion(player, Phase.CONDUCT_COMBAT, "No pending battles.")]

    suggestions: list[BotSuggestion] = []
    for i, battle in enumerate(pending[:top_k]):
        atk_count = len(battle.attacking_units)
        def_count = len(battle.defending_units)
        odds = atk_count / max(1, def_count)
        suggestions.append(BotSuggestion(
            suggestion_id=str(uuid4()),
            rank=i + 1,
            player=player,
            phase=Phase.CONDUCT_COMBAT,
            actions=[ActionItem(action_type="resolve_battle", detail=battle.battle_id)],
            score=odds * 2.0,
            score_breakdown=ScoreBreakdown(
                expected_enemy_value_destroyed=float(def_count),
                expected_own_value_lost=float(atk_count * 0.5),
                total=odds * 2.0,
            ),
            reasoning=f"Resolve battle at {battle.zone_id.replace('_', ' ')} — {atk_count} attackers vs {def_count} defenders. Attack:Defense ratio = {odds:.1f}.",
            confidence_band=ConfidenceBand.HIGH if odds > 1.5 else ConfidenceBand.MEDIUM,
        ))
    return suggestions


# ── Non-Combat Move Advisor ───────────────────────────────────────────────────

def _non_combat_advisor(state: GameState, player: Player, top_k: int) -> list[BotSuggestion]:
    idle_units = [
        u for u in state.units.values()
        if u.owner == player and not u.has_moved and not u.has_attacked
    ]
    if not idle_units:
        return [_pass_suggestion(player, Phase.NON_COMBAT_MOVE, "All units have moved.")]

    from rules_core.map_data import get_map
    md = get_map()

    capital = _find_capital_zone(state, player)
    suggestions: list[BotSuggestion] = []

    for unit in idle_units[:top_k]:
        zone_info = md.zones.get(unit.zone_id)
        if not zone_info:
            continue
        adj_friendly = [
            z for z in zone_info.adjacent
            if state.zones.get(z) and state.zones[z].owner == player
        ]
        if not adj_friendly:
            continue
        best_dest = adj_friendly[0]
        suggestions.append(BotSuggestion(
            suggestion_id=str(uuid4()),
            rank=len(suggestions) + 1,
            player=player,
            phase=Phase.NON_COMBAT_MOVE,
            actions=[ActionItem(action_type="move", unit_id=unit.unit_id, from_zone=unit.zone_id, to_zone=best_dest)],
            score=1.0,
            score_breakdown=ScoreBreakdown(positional_gain=1.0, total=1.0),
            reasoning=f"Move {unit.unit_type.value} toward capital or frontline.",
            confidence_band=ConfidenceBand.LOW,
        ))
    return suggestions[:top_k] or [_pass_suggestion(player, Phase.NON_COMBAT_MOVE)]


# ── Placement Advisor ─────────────────────────────────────────────────────────

def _placement_advisor(state: GameState, player: Player, top_k: int) -> list[BotSuggestion]:
    pending = [p for p in state.pending_placements if p.player == player]
    if not pending:
        return [_pass_suggestion(player, Phase.MOBILIZE_NEW_UNITS, "No units to place.")]

    # Find ICs controlled by player
    ic_zones = [
        zid for zid, zs in state.zones.items()
        if zs.owner == player and zs.has_industrial_complex
    ]
    if not ic_zones:
        return [_pass_suggestion(player, Phase.MOBILIZE_NEW_UNITS, "No industrial complexes available.")]

    actions = []
    for p in pending:
        best_ic = ic_zones[0]
        actions.append(ActionItem(
            action_type="place",
            unit_type=p.unit_type,
            count=p.count,
            to_zone=best_ic,
        ))

    return [BotSuggestion(
        suggestion_id=str(uuid4()),
        rank=1,
        player=player,
        phase=Phase.MOBILIZE_NEW_UNITS,
        actions=actions,
        score=2.0,
        score_breakdown=ScoreBreakdown(positional_gain=2.0, total=2.0),
        reasoning=f"Place purchased units in {ic_zones[0].replace('_', ' ')}.",
        confidence_band=ConfidenceBand.MEDIUM,
    )]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pass_suggestion(player: Player, phase: Phase, reason: str = "No action recommended.") -> BotSuggestion:
    return BotSuggestion(
        suggestion_id=str(uuid4()),
        rank=1,
        player=player,
        phase=phase,
        actions=[ActionItem(action_type="done", detail=reason)],
        score=0.0,
        score_breakdown=ScoreBreakdown(),
        reasoning=reason,
        confidence_band=ConfidenceBand.HIGH,
    )


def _economy_score(state: GameState, player: Player) -> float:
    return float(state.economy.treasury.get(player.value, 0)) / 10.0


def _has_coastal_industrial_complex(state: GameState, player: Player) -> bool:
    from rules_core.map_data import get_map
    md = get_map()
    for zone_id, zone_state in state.zones.items():
        if zone_state.owner == player and zone_state.has_industrial_complex:
            zone_info = md.zones.get(zone_id)
            if zone_info:
                adj = md.zones.get
                has_sea = any(
                    md.zones[a].zone_type.value == "sea"
                    for a in zone_info.adjacent
                    if a in md.zones
                )
                if has_sea:
                    return True
    return False


def _find_capital_zone(state: GameState, player: Player) -> str | None:
    for zone_id, zone_state in state.zones.items():
        if zone_state.is_capital and zone_state.owner == player:
            return zone_id
    return None
