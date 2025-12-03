from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import polars as pl
from skyfield.api import EarthSatellite, load, wgs84

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


def subpoint_for_satellite(sat: EarthSatellite, t) -> dict[str, float]:
    """Compute latitude, longitude, and altitude for a single satellite at time *t*.

    Returns a dict with keys: ``lat``, ``lon``, ``alt_km``.
    """
    geocentric = sat.at(t)
    sp = wgs84.subpoint(geocentric)
    return {
        "lat": sp.latitude.degrees,
        "lon": sp.longitude.degrees,
        "alt_km": sp.elevation.km,
    }


def compute_all_subpoints(t=None) -> Dict[str, dict[str, float]]:
    """Compute subpoints for all satellites at time *t* (or now if omitted)."""
    if t is None:
        t = TS.now()

    results: Dict[str, dict[str, float]] = {}
    for name, sat in SATELLITES.items():
        try:
            results[name] = subpoint_for_satellite(sat, t)
        except Exception:
            LOGGER.exception("Failed to compute subpoint for %s", name)

    return results


def initialize_satellites(
    parquet_path: str | Path = DEFAULT_PARQUET_PATH,
) -> Dict[str, EarthSatellite]:
    """Populate the global SATELLITES cache from the Parquet file."""
    global SATELLITES
    SATELLITES = load_satellites_from_parquet(parquet_path)
    return SATELLITES
