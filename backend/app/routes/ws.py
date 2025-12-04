from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from .. import state


LOGGER = logging.getLogger(__name__)
DEFAULT_WS_INTERVAL_SECONDS = 5.0
# Limit WebSocket payload size to avoid “message too big” errors.
# We stream a subset; full data is still available via /api/satellites.
WS_MAX_SATELLITES = 500


async def ws_satellites(websocket: WebSocket, interval_seconds: float = DEFAULT_WS_INTERVAL_SECONDS) -> None:
    """Stream latest satellite positions every *interval_seconds* (truncated for size)."""
    await websocket.accept()
    LOGGER.info("WebSocket client connected for /ws/satellites")

    try:
        while True:
            positions, last_updated = await state.get_positions_snapshot()
            ts = last_updated.isoformat() if last_updated else None

            # Truncate to avoid exceeding WebSocket message size limits.
            # Keep a deterministic subset (first N by name) for consistency.
            items = sorted(positions.items(), key=lambda kv: kv[0])
            truncated = dict(items[:WS_MAX_SATELLITES])
            payload = {
                "last_updated": ts,
                "satellites": truncated,
                "_note": f"Showing first {len(truncated)} satellites; use /api/satellites for full list.",
            }
            await websocket.send_json(payload)
            await asyncio.sleep(interval_seconds)
    except WebSocketDisconnect:
        LOGGER.info("WebSocket client disconnected from /ws/satellites")
    except Exception:
        LOGGER.exception("Error in WebSocket stream for /ws/satellites")
        # Attempt to close cleanly on unexpected errors
        try:
            await websocket.close()
        except Exception:
            pass
