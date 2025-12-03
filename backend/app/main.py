import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import orbits, scheduler, state
from .routes import satellites, passes, groundtrack


LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    orbits.initialize_satellites()
    if not orbits.SATELLITES:
        LOGGER.warning(
            "No satellites loaded at startup; run the TLE pipeline to generate Parquet data.",
        )
    else:
        await state.set_positions(orbits.compute_all_subpoints())

    scheduler.start_scheduler()
    try:
        yield
    finally:
        scheduler.stop_scheduler()


app = FastAPI(lifespan=lifespan)

app.include_router(satellites.router)
app.include_router(passes.router)
app.include_router(groundtrack.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
