"""Map board-coordinate detections to canonical zone IDs.

Uses the zone polygons from the map data file for polygon-in-point testing.
Board coordinates are normalized [0,1] x [0,1].
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import numpy as np

from game_schema.observation import ZoneCandidate

_MAP_JSON = Path(__file__).resolve().parents[2] / "data" / "map" / "pacific_1940_2e.json"

# Placeholder: in production, load real polygon data from the map file.
# The map currently has [[0,0],[0,0],[0,0],[0,0]] as placeholder polygons.
# This module will use real polygons once they are digitized.
_zone_polygons: dict[str, np.ndarray] | None = None


def _load_polygons() -> dict[str, np.ndarray]:
    with open(_MAP_JSON, encoding="utf-8") as f:
        data = json.load(f)
    polys: dict[str, np.ndarray] = {}
    for zone_id, zone_data in data.get("territories", {}).items():
        pts = zone_data.get("zone_polygon", [])
        if pts and any(p != [0, 0] for p in pts):
            polys[zone_id] = np.array(pts, dtype=np.float32)
    return polys


def get_zone_polygons() -> dict[str, np.ndarray]:
    global _zone_polygons
    if _zone_polygons is None:
        _zone_polygons = _load_polygons()
    return _zone_polygons


def assign_zones(
    board_coord: tuple[float, float],
    top_k: int = 3,
) -> list[ZoneCandidate]:
    """Return top-k zone candidates for a point in [0,1] x [0,1] board space."""
    polys = get_zone_polygons()
    candidates: list[ZoneCandidate] = []

    # Try polygon-in-point first
    for zone_id, poly in polys.items():
        try:
            import cv2
            inside = cv2.pointPolygonTest(poly, board_coord, False)
            if inside >= 0:
                candidates.append(ZoneCandidate(
                    zone_id=zone_id,
                    confidence=0.95 if inside > 0 else 0.75,
                    overlap_fraction=1.0 if inside > 0 else 0.5,
                ))
        except Exception:
            pass

    if not candidates:
        # Fallback: distance-based nearest zone
        candidates = _nearest_zones(board_coord, polys, top_k)

    return sorted(candidates, key=lambda c: -c.confidence)[:top_k]


def _nearest_zones(
    point: tuple[float, float],
    polys: dict[str, np.ndarray],
    top_k: int,
) -> list[ZoneCandidate]:
    """Return nearest zones by centroid distance when polygon data is sparse."""
    scored: list[tuple[str, float]] = []
    px, py = point
    for zone_id, poly in polys.items():
        if len(poly) < 1:
            continue
        cx = float(poly[:, 0].mean())
        cy = float(poly[:, 1].mean())
        dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
        scored.append((zone_id, dist))

    scored.sort(key=lambda x: x[1])
    result = []
    for zone_id, dist in scored[:top_k]:
        conf = max(0.1, 1.0 - dist * 2)
        result.append(ZoneCandidate(zone_id=zone_id, confidence=conf, overlap_fraction=0.5))
    return result
