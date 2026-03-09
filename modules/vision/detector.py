"""Unit detection and tracking using Ultralytics YOLO.

Processes camera frames and returns Detection objects ready for
reconciliation. Zone assignment uses the canonical board polygons.
"""
from __future__ import annotations
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from game_schema.enums import ConfidenceBand, UnitType, Player
from game_schema.observation import (
    BoundingBox,
    Detection,
    Observation,
    UncertaintyFlags,
    ZoneCandidate,
    ZoneObservation,
)
from .calibration import get_calibration, image_to_board_coords
from .zone_mapper import assign_zones


# Lazy-loaded YOLO model
_model = None


def _get_model(model_path: str = "models/detector.pt"):
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO
            if Path(model_path).exists():
                _model = YOLO(model_path)
            else:
                _model = None  # No model file yet — return empty detections
        except ImportError:
            _model = None
    return _model


# Class index to UnitType mapping (populated after training)
CLASS_MAP: dict[int, UnitType] = {
    0: UnitType.INFANTRY,
    1: UnitType.ARTILLERY,
    2: UnitType.ARMOR,
    3: UnitType.FIGHTER,
    4: UnitType.BOMBER,
    5: UnitType.BATTLESHIP,
    6: UnitType.CARRIER,
    7: UnitType.CRUISER,
    8: UnitType.DESTROYER,
    9: UnitType.SUBMARINE,
    10: UnitType.TRANSPORT,
}

OWNER_CLASS_MAP: dict[int, Player] = {
    0: Player.JAPAN,
    1: Player.USA,
    2: Player.UK_PACIFIC,
    3: Player.ANZAC,
    4: Player.CHINA,
}


async def process_frame(
    game_id: str, session_id: str, frame_bytes: bytes
) -> dict[str, Any]:
    """Process a raw camera frame and return detection results."""
    import cv2

    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"observation_id": str(uuid4()), "detections": [], "error": "Failed to decode frame."}

    model = _get_model()
    observation_id = str(uuid4())
    detections: list[Detection] = []
    cal = get_calibration(session_id)

    if model is not None:
        results = model.track(frame, persist=True, conf=0.4, iou=0.5)
        for result in results:
            if result.boxes is None:
                continue
            for i, box in enumerate(result.boxes):
                xyxy = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                track_id = str(int(box.id[0].cpu().numpy())) if box.id is not None else None

                unit_type = CLASS_MAP.get(cls)
                bbox = BoundingBox(x1=float(xyxy[0]), y1=float(xyxy[1]),
                                   x2=float(xyxy[2]), y2=float(xyxy[3]))
                cx, cy = bbox.center

                board_coords = image_to_board_coords((cx, cy), session_id)
                zone_candidates = assign_zones(board_coords) if board_coords else []
                best_zone = zone_candidates[0].zone_id if zone_candidates else None

                confidence_band = (
                    ConfidenceBand.HIGH if conf >= 0.85
                    else ConfidenceBand.MEDIUM if conf >= 0.60
                    else ConfidenceBand.LOW if conf >= 0.40
                    else ConfidenceBand.VERY_LOW
                )

                det = Detection(
                    track_id=track_id,
                    unit_type=unit_type,
                    class_confidence=conf,
                    overall_confidence=conf,
                    bbox=bbox,
                    centroid_board=list(board_coords) if board_coords else None,
                    zone_candidates=zone_candidates,
                    best_zone=best_zone,
                    confidence_band=confidence_band,
                )
                detections.append(det)

    uncertainty = _compute_uncertainty(detections)
    zone_obs = _build_zone_observations(detections)

    obs = Observation(
        observation_id=observation_id,
        game_id=game_id,
        session_id=session_id,
        frame_id=0,
        captured_at=datetime.utcnow(),
        is_calibrated=cal.is_calibrated,
        detections=detections,
        zone_observations=zone_obs,
        uncertainty_flags=uncertainty,
        overall_confidence=ConfidenceBand.HIGH if not uncertainty.has_low_confidence_class else ConfidenceBand.MEDIUM,
    )

    return obs.model_dump(mode="json")


def _compute_uncertainty(detections: list[Detection]) -> UncertaintyFlags:
    flags = UncertaintyFlags()
    flagged_zones: set[str] = set()

    low_conf = [d for d in detections if d.confidence_band in (ConfidenceBand.LOW, ConfidenceBand.VERY_LOW)]
    if low_conf:
        flags.has_low_confidence_class = True
        flagged_zones.update(d.best_zone for d in low_conf if d.best_zone)

    multi_zone = [d for d in detections if len(d.zone_candidates) > 1]
    if multi_zone:
        flags.has_multiple_zone_candidates = True
        for d in multi_zone:
            flagged_zones.update(c.zone_id for c in d.zone_candidates)

    occluded = [d for d in detections if d.is_occluded]
    if occluded:
        flags.has_occluded_units = True
        flagged_zones.update(d.best_zone for d in occluded if d.best_zone)

    flags.flagged_zones = list(flagged_zones)
    return flags


def _build_zone_observations(detections: list[Detection]) -> dict[str, ZoneObservation]:
    obs: dict[str, ZoneObservation] = {}
    for det in detections:
        z = det.best_zone
        if not z:
            continue
        if z not in obs:
            obs[z] = ZoneObservation(zone_id=z)
        obs[z].total_detections += 1
        if det.unit_type:
            obs[z].unit_counts[det.unit_type.value] = obs[z].unit_counts.get(det.unit_type.value, 0) + 1
    return obs
