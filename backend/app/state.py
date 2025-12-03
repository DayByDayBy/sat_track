from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict

Position = Dict[str, float]
Positions = Dict[str, Position]

POSITIONS: Positions = {}
LAST_UPDATED: datetime | None = None
_LOCK = asyncio.Lock()


async def set_positions(new_positions: Positions) -> None:
    """Replace the global positions snapshot with *new_positions*."""
    global LAST_UPDATED
    async with _LOCK:
        POSITIONS.clear()
        POSITIONS.update(new_positions)
        LAST_UPDATED = datetime.now(timezone.utc)


async def get_positions_snapshot() -> tuple[Positions, datetime | None]:
    """Return a copy of the current positions and the last updated timestamp."""
    async with _LOCK:
        return POSITIONS.copy(), LAST_UPDATED
