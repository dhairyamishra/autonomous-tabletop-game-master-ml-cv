"""Battle round resolution for WW2 Pacific 1940 2E.

Implements the full battle sequence: simultaneous fire, casualty selection,
retreat decision, loop until end condition. Fully deterministic from
(state_snapshot, choices, RNG stream).

Pure logic — no I/O.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from game_schema.enums import BattleStatus, Player, UnitStatus, UnitType
from game_schema.game_state import GameState, PendingBattle, Unit

from .rng import RngStream, make_battle_input_hash


@dataclass
class BattleCombatant:
    unit_id: str
    unit_type: UnitType
    owner: Player
    attack_value: int
    defense_value: int
    is_two_hit: bool
    hits_taken: int = 0

    @property
    def is_alive(self) -> bool:
        if self.is_two_hit:
            return self.hits_taken < 2
        return self.hits_taken < 1

    @property
    def is_damaged(self) -> bool:
        return self.is_two_hit and self.hits_taken == 1


@dataclass
class RoundResult:
    round_number: int
    attacker_rolls: list[int]
    defender_rolls: list[int]
    attacker_hits: int
    defender_hits: int
    attacker_casualties: list[str]   # unit_ids eliminated this round
    defender_casualties: list[str]
    attacker_remaining: int
    defender_remaining: int


@dataclass
class BattleResult:
    battle_id: str
    zone_id: str
    attacker: Player
    defender: Player
    status: BattleStatus
    rounds: list[RoundResult] = field(default_factory=list)
    all_attacker_losses: list[str] = field(default_factory=list)
    all_defender_losses: list[str] = field(default_factory=list)
    territory_captured: bool = False
    rng_seed: str = ""
    rng_algorithm: str = ""
    battle_input_hash: str = ""
    retreat_to_zone: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "battle_id": self.battle_id,
            "zone_id": self.zone_id,
            "attacker": self.attacker.value,
            "defender": self.defender.value,
            "status": self.status.value,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "attacker_rolls": r.attacker_rolls,
                    "defender_rolls": r.defender_rolls,
                    "attacker_hits": r.attacker_hits,
                    "defender_hits": r.defender_hits,
                    "attacker_casualties": r.attacker_casualties,
                    "defender_casualties": r.defender_casualties,
                }
                for r in self.rounds
            ],
            "all_attacker_losses": self.all_attacker_losses,
            "all_defender_losses": self.all_defender_losses,
            "territory_captured": self.territory_captured,
            "rng_seed": self.rng_seed,
            "rng_algorithm": self.rng_algorithm,
            "battle_input_hash": self.battle_input_hash,
        }


@dataclass
class BattleChoices:
    """Player decisions that affect battle flow."""
    retreat_after_round: int | None = None    # attacker retreats after this round (None = fight to the end)
    retreat_to_zone: str | None = None
    attacker_casualty_order: list[str] | None = None  # preferred unit_ids to take first
    defender_casualty_order: list[str] | None = None


UNIT_COMBAT_VALUES: dict[UnitType, tuple[int, int, bool]] = {
    UnitType.INFANTRY:   (1, 2, False),
    UnitType.ARTILLERY:  (2, 2, False),
    UnitType.ARMOR:      (3, 3, False),
    UnitType.FIGHTER:    (3, 4, False),
    UnitType.BOMBER:     (4, 1, False),
    UnitType.BATTLESHIP: (4, 4, True),
    UnitType.CARRIER:    (1, 2, False),
    UnitType.CRUISER:    (3, 3, False),
    UnitType.DESTROYER:  (2, 2, False),
    UnitType.SUBMARINE:  (2, 1, False),
    UnitType.TRANSPORT:  (0, 0, False),
}


def _make_combatants(unit_ids: list[str], state: GameState) -> list[BattleCombatant]:
    combatants = []
    for uid in unit_ids:
        unit = state.units.get(uid)
        if unit is None or unit.status in (UnitStatus.SUNK, UnitStatus.DESTROYED):
            continue
        atk, dfn, two_hit = UNIT_COMBAT_VALUES.get(unit.unit_type, (0, 0, False))
        combatants.append(BattleCombatant(
            unit_id=uid,
            unit_type=unit.unit_type,
            owner=unit.owner,
            attack_value=atk,
            defense_value=dfn,
            is_two_hit=two_hit,
            hits_taken=unit.hits_taken,
        ))
    return combatants


def _roll_hits(combatants: list[BattleCombatant], is_attacker: bool, rng: RngStream) -> tuple[list[int], int]:
    rolls = rng.roll_n(len(combatants))
    hits = 0
    for combatant, roll in zip(combatants, rolls):
        threshold = combatant.attack_value if is_attacker else combatant.defense_value
        if threshold > 0 and roll <= threshold:
            hits += 1
    return rolls, hits


def _select_casualties(
    combatants: list[BattleCombatant],
    hits: int,
    preferred_order: list[str] | None,
) -> tuple[list[str], list[BattleCombatant]]:
    """Remove up to `hits` casualties. Returns (eliminated unit_ids, remaining combatants)."""
    if hits <= 0:
        return [], combatants

    # Sort by combat value ascending (cheapest first = standard rule)
    # Then by preferred order if supplied
    order = list(combatants)
    if preferred_order:
        id_rank = {uid: i for i, uid in enumerate(preferred_order)}
        order.sort(key=lambda c: id_rank.get(c.unit_id, 9999))
    else:
        order.sort(key=lambda c: c.attack_value + c.defense_value)

    eliminated: list[str] = []
    remaining: list[BattleCombatant] = list(combatants)
    hits_left = hits

    for combatant in order:
        if hits_left <= 0:
            break
        if not combatant.is_alive:
            continue
        if combatant.unit_type == UnitType.TRANSPORT:
            continue  # transports taken last

        if combatant.is_two_hit and not combatant.is_damaged:
            combatant.hits_taken += 1
            hits_left -= 1
        else:
            combatant.hits_taken = 2 if combatant.is_two_hit else 1
            eliminated.append(combatant.unit_id)
            hits_left -= 1

    # Take transports last
    for combatant in order:
        if hits_left <= 0:
            break
        if combatant.unit_type == UnitType.TRANSPORT and combatant.is_alive:
            combatant.hits_taken = 1
            eliminated.append(combatant.unit_id)
            hits_left -= 1

    remaining = [c for c in remaining if c.unit_id not in eliminated]
    return eliminated, remaining


def resolve_battle(
    state: GameState,
    battle: PendingBattle,
    choices: BattleChoices | None = None,
    rng: RngStream | None = None,
) -> BattleResult:
    """Fully resolve a battle and return the result.

    Does NOT mutate state — caller applies the result.
    This function is deterministic given (state, battle, choices, rng).
    """
    choices = choices or BattleChoices()
    rng = rng or RngStream.from_new_seed()

    input_hash = make_battle_input_hash(
        battle.battle_id,
        [{"unit_id": uid} for uid in battle.attacking_units],
        [{"unit_id": uid} for uid in battle.defending_units],
        battle.zone_id,
    )

    attackers = _make_combatants(battle.attacking_units, state)
    defenders = _make_combatants(battle.defending_units, state)

    result = BattleResult(
        battle_id=battle.battle_id,
        zone_id=battle.zone_id,
        attacker=battle.attacker,
        defender=battle.defender,
        status=BattleStatus.IN_PROGRESS,
        rng_seed=rng.seed,
        rng_algorithm=rng.algorithm,
        battle_input_hash=input_hash,
    )

    round_num = 0

    while True:
        round_num += 1
        active_attackers = [c for c in attackers if c.is_alive]
        active_defenders = [c for c in defenders if c.is_alive]

        if not active_attackers or not active_defenders:
            break

        # Simultaneous fire
        atk_rolls, atk_hits = _roll_hits(active_attackers, is_attacker=True, rng=rng)
        def_rolls, def_hits = _roll_hits(active_defenders, is_attacker=False, rng=rng)

        # Apply casualties
        atk_cas, attackers = _select_casualties(
            active_attackers, def_hits, choices.attacker_casualty_order
        )
        def_cas, defenders = _select_casualties(
            active_defenders, atk_hits, choices.defender_casualty_order
        )

        round_result = RoundResult(
            round_number=round_num,
            attacker_rolls=atk_rolls,
            defender_rolls=def_rolls,
            attacker_hits=atk_hits,
            defender_hits=def_hits,
            attacker_casualties=atk_cas,
            defender_casualties=def_cas,
            attacker_remaining=len([c for c in attackers if c.is_alive]),
            defender_remaining=len([c for c in defenders if c.is_alive]),
        )
        result.rounds.append(round_result)
        result.all_attacker_losses.extend(atk_cas)
        result.all_defender_losses.extend(def_cas)

        alive_atk = [c for c in attackers if c.is_alive]
        alive_def = [c for c in defenders if c.is_alive]

        # Check end conditions
        if not alive_atk and not alive_def:
            result.status = BattleStatus.DRAWN
            break
        if not alive_atk:
            result.status = BattleStatus.DEFENDER_WON
            break
        if not alive_def:
            result.status = BattleStatus.ATTACKER_WON
            result.territory_captured = True
            break

        # Check retreat
        if choices.retreat_after_round == round_num:
            result.status = BattleStatus.ATTACKER_RETREATED
            result.retreat_to_zone = choices.retreat_to_zone
            break

    return result
