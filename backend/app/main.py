import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import orbits


LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    orbits.initialize_satellites()
    if not orbits.SATELLITES:
        LOGGER.warning(
            "No satellites loaded at startup; run the TLE pipeline to generate Parquet data.",
        )
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
