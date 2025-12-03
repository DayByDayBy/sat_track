from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import orbits


router = APIRouter(prefix="/api")


@router.get("/passes")
async def get_passes(
    lat: float = Query(..., description="Observer latitude in degrees (-90 to 90)"),
    lon: float = Query(..., description="Observer longitude in degrees (-180 to 180)"),
    sat_id: str = Query(..., description="Satellite identifier (currently name)"),
    hours: float = Query(24.0, gt=0.0, le=48.0, description="Prediction window in hours"),
    min_elevation_deg: float = Query(0.0, ge=0.0, le=90.0, description="Minimum elevation for pass events"),
) -> dict:
    """Predict satellite passes over the next *hours* for an observer.

    Returns a list of passes with rise/culmination/set times and max elevation.
    """
    if not (-90.0 <= lat <= 90.0):
        raise HTTPException(status_code=400, detail="lat must be between -90 and 90 degrees")
    if not (-180.0 <= lon <= 180.0):
        raise HTTPException(status_code=400, detail="lon must be between -180 and 180 degrees")

    sat = orbits.SATELLITES.get(sat_id)
    if sat is None:
        raise HTTPException(status_code=404, detail=f"Satellite '{sat_id}' not found")

    passes = orbits.compute_passes_for_observer(
        sat,
        lat_deg=lat,
        lon_deg=lon,
        hours=hours,
        min_elevation_deg=min_elevation_deg,
    )

    return {
        "sat_id": sat_id,
        "observer": {"lat": lat, "lon": lon},
        "hours": hours,
        "min_elevation_deg": min_elevation_deg,
        "passes": passes,
    }
