from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from .. import state


router = APIRouter(prefix="/api")


@router.get("/satellites")
async def get_satellites() -> dict:
    """Return the latest global satellite positions.

    Response shape:
        {
            "last_updated": ISO8601 | null,
            "satellites": { name: { "lat": float, "lon": float, "alt_km": float } }
        }
    """
    positions, last_updated = await state.get_positions_snapshot()
    ts: str | None
    if isinstance(last_updated, datetime):
        ts = last_updated.isoformat()
    else:
        ts = None

    return {
        "last_updated": ts,
        "satellites": positions,
    }
