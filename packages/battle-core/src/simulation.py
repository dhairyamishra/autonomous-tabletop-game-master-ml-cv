"""Monte Carlo battle simulation for the bot advisor.

Runs many simulated battles to estimate win probabilities and expected losses.
Pure logic — no I/O.
"""
from __future__ import annotations
from dataclasses import dataclass

from game_schema.game_state import GameState, PendingBattle

from .resolution import BattleChoices, BattleResult, resolve_battle
from .rng import RngStream


@dataclass
class SimStats:
    simulations: int
    attacker_wins: int
    defender_wins: int
    draws: int
    retreats: int
    attacker_win_rate: float
    expected_attacker_losses: float   # average units lost
    expected_defender_losses: float
    expected_ipc_swing: float         # attacker net IPC gain (positive = attacker ahead)


def simulate_battle(
    state: GameState,
    battle: PendingBattle,
    n_simulations: int = 200,
) -> SimStats:
    """Run n_simulations of a battle and return aggregate statistics."""
    from rules_core.map_data import get_map
    md = get_map()

    def _ipc(uid: str) -> int:
        unit = state.units.get(uid)
        if not unit:
            return 0
        return md.unit_costs.get(unit.unit_type.value, 0)

    attacker_wins = 0
    defender_wins = 0
    draws = 0
    retreats = 0
    total_atk_losses = 0.0
    total_def_losses = 0.0
    total_ipc_swing = 0.0

    for _ in range(n_simulations):
        rng = RngStream.from_new_seed()
        result: BattleResult = resolve_battle(state, battle, BattleChoices(), rng)

        if result.status.value == "attacker_won":
            attacker_wins += 1
        elif result.status.value == "defender_won":
            defender_wins += 1
        elif result.status.value == "drawn":
            draws += 1
        else:
            retreats += 1

        atk_loss_ipc = sum(_ipc(uid) for uid in result.all_attacker_losses)
        def_loss_ipc = sum(_ipc(uid) for uid in result.all_defender_losses)
        total_atk_losses += len(result.all_attacker_losses)
        total_def_losses += len(result.all_defender_losses)
        total_ipc_swing += def_loss_ipc - atk_loss_ipc

    n = n_simulations
    return SimStats(
        simulations=n,
        attacker_wins=attacker_wins,
        defender_wins=defender_wins,
        draws=draws,
        retreats=retreats,
        attacker_win_rate=attacker_wins / n,
        expected_attacker_losses=total_atk_losses / n,
        expected_defender_losses=total_def_losses / n,
        expected_ipc_swing=total_ipc_swing / n,
    )
