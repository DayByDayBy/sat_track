from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from . import orbits, state


LOGGER = logging.getLogger(__name__)
DEFAULT_INTERVAL_SECONDS = 5.0

_scheduler: Optional[AsyncIOScheduler] = None


async def update_positions_job() -> None:
    """Background job: recompute all satellite positions and store snapshot."""
    if not orbits.SATELLITES:
        LOGGER.warning("No satellites available; skipping position update job")
        return

    positions = orbits.compute_all_subpoints()
    await state.set_positions(positions)
    LOGGER.info("Updated positions for %d satellites", len(positions))


def start_scheduler(interval_seconds: float = DEFAULT_INTERVAL_SECONDS) -> AsyncIOScheduler:
    """Start the APScheduler instance if it isn't already running."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        update_positions_job,
        trigger=IntervalTrigger(seconds=interval_seconds),
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    LOGGER.info("Started scheduler with %.1f second interval", interval_seconds)
    return scheduler


def stop_scheduler() -> None:
    """Stop the APScheduler instance if it is running."""
    global _scheduler
    if _scheduler is None:
        return

    _scheduler.shutdown(wait=False)
    LOGGER.info("Stopped scheduler")
    _scheduler = None
