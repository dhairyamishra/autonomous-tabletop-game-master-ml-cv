"""Phase state machine for WW2 Pacific 1940 2E.

Manages turn order, phase transitions, and phase validity checks.
Pure logic — no I/O.
"""
from __future__ import annotations
from dataclasses import dataclass

from game_schema.enums import Phase, Player, PHASE_ORDER, PLAYER_ORDER
from game_schema.game_state import GameState


@dataclass
class PhaseTransitionResult:
    success: bool
    reason: str = ""
    new_phase: Phase | None = None
    new_player: Player | None = None
    new_round: int | None = None


def can_advance_phase(state: GameState) -> tuple[bool, str]:
    """Check whether the current phase can be ended.

    Returns (can_advance, reason_if_blocked).
    """
    phase = state.turn.phase
    player = state.turn.current_player

    if phase == Phase.SETUP:
        return True, ""

    if phase == Phase.CONDUCT_COMBAT:
        unresolved = [
            b for b in state.pending_battles.values()
            if b.status.value == "pending" or b.status.value == "in_progress"
        ]
        if unresolved:
            return False, f"{len(unresolved)} battle(s) still unresolved."

    if phase == Phase.MOBILIZE_NEW_UNITS:
        unplaced = [
            p for p in state.pending_placements
            if p.player == player and p.zone_id is None
        ]
        if unplaced:
            return False, f"{len(unplaced)} purchased unit(s) not yet placed."

    return True, ""


def advance_phase(state: GameState) -> PhaseTransitionResult:
    """Compute the next phase/player/round without mutating state.

    Caller is responsible for applying the returned values.
    """
    can, reason = can_advance_phase(state)
    if not can:
        return PhaseTransitionResult(False, reason)

    current_phase = state.turn.phase
    current_player = state.turn.current_player
    current_round = state.turn.round

    if current_phase == Phase.SETUP:
        return PhaseTransitionResult(
            True,
            new_phase=Phase.PURCHASE,
            new_player=current_player,
            new_round=current_round,
        )

    phase_idx = PHASE_ORDER.index(current_phase) if current_phase in PHASE_ORDER else -1

    # If not the last phase of the turn, advance to next phase
    if phase_idx < len(PHASE_ORDER) - 1:
        next_phase = PHASE_ORDER[phase_idx + 1]
        return PhaseTransitionResult(
            True,
            new_phase=next_phase,
            new_player=current_player,
            new_round=current_round,
        )

    # End of TURN_END — advance to next player or new round
    player_idx = PLAYER_ORDER.index(current_player)
    if player_idx < len(PLAYER_ORDER) - 1:
        next_player = PLAYER_ORDER[player_idx + 1]
        return PhaseTransitionResult(
            True,
            new_phase=Phase.PURCHASE,
            new_player=next_player,
            new_round=current_round,
        )

    # All players done — new round
    return PhaseTransitionResult(
        True,
        new_phase=Phase.PURCHASE,
        new_player=PLAYER_ORDER[0],  # Japan starts
        new_round=current_round + 1,
    )


def get_legal_phases_for_action(action_type: str) -> list[Phase]:
    """Return which phases allow a given action type."""
    mapping: dict[str, list[Phase]] = {
        "purchase":         [Phase.PURCHASE],
        "combat_move":      [Phase.COMBAT_MOVE],
        "declare_battle":   [Phase.COMBAT_MOVE, Phase.CONDUCT_COMBAT],
        "resolve_battle":   [Phase.CONDUCT_COMBAT],
        "non_combat_move":  [Phase.NON_COMBAT_MOVE],
        "place_unit":       [Phase.MOBILIZE_NEW_UNITS],
        "collect_income":   [Phase.COLLECT_INCOME],
        "advance_phase":    list(Phase),
    }
    return mapping.get(action_type, [])


def is_action_legal_in_phase(action_type: str, phase: Phase) -> bool:
    return phase in get_legal_phases_for_action(action_type)
