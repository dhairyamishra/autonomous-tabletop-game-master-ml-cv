"""battle-core: pure combat logic for WW2 Pacific 1940 2E. No I/O."""
from .resolution import (
    BattleCombatant,
    BattleChoices,
    BattleResult,
    RoundResult,
    UNIT_COMBAT_VALUES,
    resolve_battle,
)
from .rng import (
    RNG_ALGORITHM_VERSION,
    RngStream,
    make_battle_input_hash,
)
from .simulation import SimStats, simulate_battle

__all__ = [
    "BattleCombatant", "BattleChoices", "BattleResult", "RoundResult",
    "UNIT_COMBAT_VALUES", "resolve_battle",
    "RNG_ALGORITHM_VERSION", "RngStream", "make_battle_input_hash",
    "SimStats", "simulate_battle",
]
