"""Server-side RNG for combat resolution.

Uses Python's secrets module (CSPRNG) for dice rolls.
Every battle stores the seed reference and ordered roll list for full replay.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from typing import Any


RNG_ALGORITHM_VERSION = "battle-core-v1-csprng"


@dataclass
class RngStream:
    """A deterministic stream of d6 rolls generated from a seed."""
    seed: str                           # hex seed string
    algorithm: str = RNG_ALGORITHM_VERSION
    rolls: list[int] = field(default_factory=list)
    _index: int = field(default=0, repr=False)

    def next_roll(self) -> int:
        """Return the next roll from the stream, extending it if needed."""
        while self._index >= len(self.rolls):
            self._extend()
        roll = self.rolls[self._index]
        self._index += 1
        return roll

    def roll_n(self, n: int) -> list[int]:
        return [self.next_roll() for _ in range(n)]

    def _extend(self, batch: int = 64) -> None:
        """Generate more rolls deterministically from seed + current length."""
        base = f"{self.seed}:{len(self.rolls)}"
        for i in range(batch):
            h = hmac.new(
                key=self.seed.encode(),
                msg=f"{len(self.rolls) + i}".encode(),
                digestmod=hashlib.sha256,
            ).digest()
            # Map first byte to 1–6
            self.rolls.append((h[0] % 6) + 1)

    @classmethod
    def from_new_seed(cls) -> "RngStream":
        seed = secrets.token_hex(32)
        return cls(seed=seed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "algorithm": self.algorithm,
            "rolls": self.rolls,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RngStream":
        obj = cls(seed=d["seed"], algorithm=d["algorithm"])
        obj.rolls = list(d["rolls"])
        return obj


def make_battle_input_hash(
    battle_id: str,
    attacking_units: list[dict[str, Any]],
    defending_units: list[dict[str, Any]],
    zone_id: str,
) -> str:
    """Deterministic hash of the battle inputs for audit/verification."""
    payload = json.dumps({
        "battle_id": battle_id,
        "zone_id": zone_id,
        "attacking_units": sorted(attacking_units, key=lambda u: u.get("unit_id", "")),
        "defending_units": sorted(defending_units, key=lambda u: u.get("unit_id", "")),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
