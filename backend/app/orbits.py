from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import polars as pl
from skyfield.api import EarthSatellite, load

from .tle_pipeline import DEFAULT_PARQUET_PATH


LOGGER = logging.getLogger(__name__)

TS = load.timescale()

# Global cache of satellites, populated at startup.
SATELLITES: Dict[str, EarthSatellite] = {}


def load_satellites_from_parquet(
    parquet_path: str | Path = DEFAULT_PARQUET_PATH,
) -> Dict[str, EarthSatellite]:
    """Load satellites from a Parquet file into a dict keyed by name.

    If the Parquet file does not exist, returns an empty dict and logs a warning.
    """
    path = Path(parquet_path)
    if not path.exists():
        LOGGER.warning("Parquet file %s does not exist; no satellites loaded", path)
        return {}

    df = pl.read_parquet(str(path))

    satellites: Dict[str, EarthSatellite] = {}
    for row in df.iter_rows(named=True):
        name = row.get("name")
        line1 = row.get("line1")
        line2 = row.get("line2")
        if not (name and line1 and line2):
            continue

        sat = EarthSatellite(line1, line2, name=name, ts=TS)
        satellites[name] = sat

    LOGGER.info("Loaded %d satellites from %s", len(satellites), path)
    return satellites


def initialize_satellites(
    parquet_path: str | Path = DEFAULT_PARQUET_PATH,
) -> Dict[str, EarthSatellite]:
    """Populate the global SATELLITES cache from the Parquet file."""
    global SATELLITES
    SATELLITES = load_satellites_from_parquet(parquet_path)
    return SATELLITES
