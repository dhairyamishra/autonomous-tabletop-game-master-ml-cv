"""Reconciliation layer: turns CV observations into proposed state deltas.

Takes the latest observation and the current official state, and produces
a proposed delta that the operator can confirm, modify, or reject.

CV observations are evidence only — this module never commits to official state.
"""
from __future__ import annotations
from typing import Any

from game_schema.enums import ConfidenceBand, Phase, Player
from game_schema.game_state import GameState
from game_schema.observation import Observation


def propose_delta(
    state: GameState,
    observation_id: str,
    observation: Observation | None = None,
) -> dict[str, Any]:
    """Produce a proposed delta from the latest observation vs official state.

    Returns:
      - proposed_deltas: list of zone-level changes
      - ambiguity_flags: zones with unresolved ambiguity
      - requires_confirmation: True if any delta needs operator sign-off
    """
    if observation is None:
        return {
            "game_id": state.game_id,
            "observation_id": observation_id,
            "proposed_deltas": [],
            "ambiguity_flags": [],
            "requires_confirmation": False,
            "message": "No observation provided.",
        }

    phase = state.turn.phase
    deltas: list[dict[str, Any]] = []
    ambiguities: list[str] = []

    # Compare each zone's observed unit counts vs official state
    for zone_id, zone_obs in observation.zone_observations.items():
        official_zone = state.zones.get(zone_id)
        if official_zone is None:
            continue

        official_units = [
            u for u in state.units.values()
            if u.zone_id == zone_id
        ]
        official_counts: dict[str, int] = {}
        for u in official_units:
            official_counts[u.unit_type.value] = official_counts.get(u.unit_type.value, 0) + 1

        # Find differences
        all_types = set(official_counts) | set(zone_obs.unit_counts)
        for unit_type in all_types:
            obs_count = zone_obs.unit_counts.get(unit_type, 0)
            off_count = official_counts.get(unit_type, 0)
            if obs_count != off_count:
                delta_count = obs_count - off_count
                deltas.append({
                    "zone_id": zone_id,
                    "unit_type": unit_type,
                    "official_count": off_count,
                    "observed_count": obs_count,
                    "delta": delta_count,
                    "confidence": _delta_confidence(zone_obs, unit_type),
                    "phase_consistent": _is_phase_consistent(phase, delta_count),
                })

        if zone_obs.has_uncertainty:
            ambiguities.append(zone_id)
            ambiguities.extend(zone_obs.uncertainty_reasons)

    requires_confirmation = bool(ambiguities) or any(
        d["confidence"] < 0.7 or not d["phase_consistent"]
        for d in deltas
    )

    return {
        "game_id": state.game_id,
        "observation_id": observation_id,
        "proposed_deltas": deltas,
        "ambiguity_flags": list(set(ambiguities)),
        "requires_confirmation": requires_confirmation,
        "delta_count": len(deltas),
    }


def _delta_confidence(zone_obs: Any, unit_type: str) -> float:
    """Estimate confidence for a specific unit_type change in this zone."""
    if zone_obs.has_uncertainty:
        return 0.4
    if zone_obs.total_detections == 0:
        return 0.5
    return 0.85


def _is_phase_consistent(phase: Phase, delta: int) -> bool:
    """Check if a count change is plausible for the current phase."""
    if phase == Phase.SETUP:
        return True  # any change is plausible during setup
    if phase in (Phase.COMBAT_MOVE, Phase.NON_COMBAT_MOVE):
        return True  # units moving around is expected
    if phase == Phase.CONDUCT_COMBAT:
        return delta <= 0  # units should only disappear (casualties)
    if phase == Phase.MOBILIZE_NEW_UNITS:
        return delta >= 0  # units should only appear (placement)
    return True


def filter_by_confidence(
    deltas: list[dict[str, Any]],
    min_confidence: float = 0.7,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split deltas into high-confidence (auto-approvable) and low-confidence (need review)."""
    high = [d for d in deltas if d["confidence"] >= min_confidence and d.get("phase_consistent", True)]
    low = [d for d in deltas if d["confidence"] < min_confidence or not d.get("phase_consistent", True)]
    return high, low
