"""Observation schema for the WW2 Pacific 1940 2E vision pipeline.

An observation represents what the camera saw at a specific moment.
It is evidence only — it never directly mutates the official game state.
"""
from __future__ import annotations
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from enums import ConfidenceBand, UnitType, Player


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


class Mask(BaseModel):
    """Instance segmentation mask as a polygon."""
    polygon: list[list[float]]  # list of [x, y] points in image coords


class ZoneCandidate(BaseModel):
    zone_id: str
    confidence: float               # 0.0 – 1.0
    overlap_fraction: float         # fraction of detection centroid within this zone


class Detection(BaseModel):
    detection_id: str = Field(default_factory=lambda: str(uuid4()))
    track_id: str | None = None         # stable tracker ID across frames
    unit_type: UnitType | None = None   # None if class unclear
    owner: Player | None = None         # None if faction unclear
    class_confidence: float = 0.0       # confidence in unit_type classification
    owner_confidence: float = 0.0       # confidence in owner classification
    overall_confidence: float = 0.0

    bbox: BoundingBox
    mask: Mask | None = None            # available if instance segmentation model used
    centroid_board: list[float] | None = None  # [x, y] in canonical board coordinates

    zone_candidates: list[ZoneCandidate] = Field(default_factory=list)
    best_zone: str | None = None

    is_occluded: bool = False
    is_stacked: bool = False            # part of a stack of multiple units
    occlusion_fraction: float = 0.0
    confidence_band: ConfidenceBand = ConfidenceBand.LOW


class ZoneObservation(BaseModel):
    zone_id: str
    unit_counts: dict[str, int] = Field(default_factory=dict)   # unit_type -> count
    owner_candidates: list[Player] = Field(default_factory=list)
    total_detections: int = 0
    has_uncertainty: bool = False
    uncertainty_reasons: list[str] = Field(default_factory=list)


class BoardTransform(BaseModel):
    homography_matrix: list[list[float]] | None = None
    board_corners_image: list[list[float]] | None = None  # 4 corners [x,y] in image coords
    board_corners_board: list[list[float]] | None = None  # 4 corners in canonical board coords
    is_calibrated: bool = False
    calibrated_at: datetime | None = None
    calibration_confidence: float = 0.0


class UncertaintyFlags(BaseModel):
    has_overlapping_units: bool = False
    has_occluded_units: bool = False
    has_low_confidence_class: bool = False
    has_unstable_tracks: bool = False
    has_impossible_count_jump: bool = False
    has_multiple_zone_candidates: bool = False
    flagged_zones: list[str] = Field(default_factory=list)
    flagged_detection_ids: list[str] = Field(default_factory=list)


class Observation(BaseModel):
    """A single camera frame observation. Evidence only — not authoritative."""

    observation_id: str = Field(default_factory=lambda: str(uuid4()))
    game_id: str
    session_id: str
    frame_id: int
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    processing_latency_ms: float = 0.0

    camera_id: str = "primary"
    board_transform: BoardTransform = Field(default_factory=BoardTransform)
    is_calibrated: bool = False

    detections: list[Detection] = Field(default_factory=list)
    zone_observations: dict[str, ZoneObservation] = Field(default_factory=dict)

    uncertainty_flags: UncertaintyFlags = Field(default_factory=UncertaintyFlags)
    overall_confidence: ConfidenceBand = ConfidenceBand.LOW

    requires_confirmation: bool = False
    confirmation_reasons: list[str] = Field(default_factory=list)
