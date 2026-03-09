"""Board calibration: homography-based perspective correction.

Uses OpenCV to find the physical board corners and compute a top-down
homography matrix that maps camera pixels to canonical board coordinates.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np


# Canonical board corners in normalized board space [0,1] x [0,1]
# Top-left, top-right, bottom-right, bottom-left
BOARD_CORNERS_CANONICAL = np.array([
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
], dtype=np.float32)


class CalibrationState:
    def __init__(self) -> None:
        self.is_calibrated = False
        self.homography: np.ndarray | None = None
        self.board_corners_image: np.ndarray | None = None
        self.calibrated_at: datetime | None = None
        self.confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_calibrated": self.is_calibrated,
            "homography_matrix": self.homography.tolist() if self.homography is not None else None,
            "board_corners_image": self.board_corners_image.tolist() if self.board_corners_image is not None else None,
            "calibrated_at": self.calibrated_at.isoformat() if self.calibrated_at else None,
            "calibration_confidence": self.confidence,
        }


# Per-session calibration states
_calibrations: dict[str, CalibrationState] = {}


def get_calibration(session_id: str) -> CalibrationState:
    if session_id not in _calibrations:
        _calibrations[session_id] = CalibrationState()
    return _calibrations[session_id]


async def run_calibration(session_id: str, camera_index: int = 0) -> dict[str, Any]:
    """Capture a frame and attempt to find the board corners.

    Uses ArUco markers or a simple rectangle detector for V1.
    Returns calibration result dict.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return {
            "is_calibrated": False,
            "message": "Camera not accessible.",
        }

    ret, frame = cap.read()
    cap.release()
    if not ret:
        return {"is_calibrated": False, "message": "Failed to capture frame."}

    cal = get_calibration(session_id)
    corners = _detect_board_corners(frame)

    if corners is None:
        return {
            "is_calibrated": False,
            "message": "Board corners not detected. Adjust camera position.",
        }

    h_img = frame.shape[0]
    w_img = frame.shape[1]
    dst = BOARD_CORNERS_CANONICAL * np.array([[w_img, h_img]], dtype=np.float32)
    H, _ = cv2.findHomography(corners, dst)

    cal.is_calibrated = True
    cal.homography = H
    cal.board_corners_image = corners
    cal.calibrated_at = datetime.utcnow()
    cal.confidence = 0.95

    return {
        "is_calibrated": True,
        "message": "Calibration successful.",
        **cal.to_dict(),
    }


def rectify_frame(frame: np.ndarray, session_id: str) -> np.ndarray | None:
    """Warp camera frame to canonical top-down view."""
    cal = get_calibration(session_id)
    if not cal.is_calibrated or cal.homography is None:
        return None
    h, w = frame.shape[:2]
    return cv2.warpPerspective(frame, cal.homography, (w, h))


def image_to_board_coords(
    point_image: tuple[float, float], session_id: str
) -> tuple[float, float] | None:
    """Map a pixel in the raw image to canonical board coordinates [0,1] x [0,1]."""
    cal = get_calibration(session_id)
    if not cal.is_calibrated or cal.homography is None:
        return None
    pt = np.array([[[point_image[0], point_image[1]]]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(pt, cal.homography)
    h = 480  # placeholder height — caller should supply actual frame height
    w = 640
    return float(transformed[0][0][0] / w), float(transformed[0][0][1] / h)


def _detect_board_corners(frame: np.ndarray) -> np.ndarray | None:
    """Detect 4 board corners using ArUco markers or contour detection.

    V1: uses contour-based rectangle detection as fallback.
    Production: replace with ArUco marker detection for robustness.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_quad: np.ndarray | None = None
    best_area = 0.0
    h, w = frame.shape[:2]
    min_area = (w * h) * 0.1  # board must be at least 10% of image

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4 and area > best_area:
            best_area = area
            best_quad = approx.reshape(4, 2).astype(np.float32)

    if best_quad is None:
        return None

    # Sort corners: top-left, top-right, bottom-right, bottom-left
    s = best_quad.sum(axis=1)
    diff = np.diff(best_quad, axis=1)
    ordered = np.array([
        best_quad[np.argmin(s)],
        best_quad[np.argmin(diff)],
        best_quad[np.argmax(s)],
        best_quad[np.argmax(diff)],
    ], dtype=np.float32)

    return ordered
