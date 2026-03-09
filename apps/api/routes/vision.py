"""Vision and camera calibration endpoints."""
from __future__ import annotations
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import EventRecord
from ..state_store import get_store

router = APIRouter(prefix="/vision", tags=["Vision"])


class CalibrateRequest(BaseModel):
    session_id: str
    game_id: str


@router.post("/calibrate")
async def calibrate_camera(
    req: CalibrateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger board calibration from the current camera frame."""
    try:
        from modules.vision.calibration import run_calibration
        result = await run_calibration(req.session_id)
    except ImportError:
        return {
            "session_id": req.session_id,
            "is_calibrated": False,
            "message": "Vision module not yet available (CV dependencies not installed).",
        }
    except Exception as e:
        raise HTTPException(500, f"Calibration failed: {e}")

    if result.get("is_calibrated"):
        db.add(EventRecord(
            session_id=req.session_id,
            game_id=req.game_id,
            event_id=str(uuid.uuid4()),
            event_type="calibration_completed",
            actor="system",
            state_version_before=0,
            state_version_after=0,
            event_json={
                "event_type": "calibration_completed",
                "session_id": req.session_id,
                "game_id": req.game_id,
                **result,
            },
        ))

    return result


@router.post("/observe-frame")
async def observe_frame(
    game_id: str,
    session_id: str,
    frame: UploadFile = File(...),
) -> dict[str, Any]:
    """Process a camera frame and return detections + zone assignments."""
    frame_bytes = await frame.read()
    try:
        from modules.vision.detector import process_frame
        result = await process_frame(game_id, session_id, frame_bytes)
    except ImportError:
        return {
            "observation_id": str(uuid.uuid4()),
            "game_id": game_id,
            "session_id": session_id,
            "is_calibrated": False,
            "detections": [],
            "message": "Vision module not yet available.",
        }
    return result


@router.post("/reconcile/propose")
async def propose_reconciliation(
    game_id: str,
    session_id: str,
    observation_id: str,
) -> dict[str, Any]:
    """Propose a state delta based on the latest observation vs official state."""
    store = get_store()
    state = await store.get(game_id)
    if state is None:
        raise HTTPException(404, "Game not found.")

    try:
        from modules.reconciliation.reconciler import propose_delta
        result = propose_delta(state, observation_id)
    except ImportError:
        return {
            "game_id": game_id,
            "observation_id": observation_id,
            "proposed_deltas": [],
            "ambiguity_flags": [],
            "requires_confirmation": False,
            "message": "Reconciliation module not yet available.",
        }
    return result
