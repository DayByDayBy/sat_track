from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import orbits


router = APIRouter(prefix="/api")


@router.get("/groundtrack")
async def get_groundtrack(
    sat_id: str = Query(..., description="Satellite identifier (currently name)"),
    hours: float = Query(1.0, gt=0.0, le=48.0, description="Prediction window in hours"),
    samples: int = Query(60, ge=2, le=500, description="Number of sample points"),
) -> dict:
    """Return sampled ground track points for the given satellite."""
    sat = orbits.SATELLITES.get(sat_id)
    if sat is None:
        raise HTTPException(status_code=404, detail=f"Satellite '{sat_id}' not found")

    track = orbits.compute_groundtrack(sat, hours=hours, samples=samples)

    return {
        "sat_id": sat_id,
        "hours": hours,
        "samples": samples,
        "points": track,
    }
