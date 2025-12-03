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


def compute_passes_for_observer(
    sat: EarthSatellite,
    lat_deg: float,
    lon_deg: float,
    hours: float = 24.0,
    min_elevation_deg: float = 0.0,
) -> list[dict[str, float | str]]:
    """Compute rise/culmination/set passes for *sat* over the next *hours*.

    Returns a list of dicts with ISO8601 timestamps and max elevation in degrees.
    """
    observer = wgs84.latlon(latitude_degrees=lat_deg, longitude_degrees=lon_deg, elevation_m=0.0)

    t0 = TS.now()
    t1 = t0 + hours / 24.0

    times, events = sat.find_events(observer, t0, t1, altitude_degrees=min_elevation_deg)

    passes: list[dict[str, float | str]] = []
    current_start = None
    current_peak = None

    for t, event in zip(times, events):
        if event == 0:  # rise
            current_start = t
            current_peak = None
        elif event == 1 and current_start is not None:  # culminate
            current_peak = t
        elif event == 2 and current_start is not None and current_peak is not None:  # set
            # Compute elevation at peak
            difference = sat - observer
            topocentric = difference.at(current_peak)
            alt, az, distance = topocentric.altaz()
            max_elev = float(alt.degrees)

            passes.append(
                {
                    "start": current_start.utc_datetime().isoformat(),
                    "peak": current_peak.utc_datetime().isoformat(),
                    "end": t.utc_datetime().isoformat(),
                    "max_elevation_deg": max_elev,
                },
            )

            current_start = None
            current_peak = None

    return passes


def compute_groundtrack(
    sat: EarthSatellite,
    hours: float = 1.0,
    samples: int = 60,
) -> list[dict[str, float | str]]:
    """Sample the satellite subpoint over the next *hours* at *samples* intervals."""
    if samples < 2:
        raise ValueError("samples must be >= 2")

    t0 = TS.now()
    track: list[dict[str, float | str]] = []

    for i in range(samples):
        fraction = i / (samples - 1)
        t = t0 + (hours / 24.0) * fraction
        geocentric = sat.at(t)
        sp = wgs84.subpoint(geocentric)
        track.append(
            {
                "time": t.utc_datetime().isoformat(),
                "lat": sp.latitude.degrees,
                "lon": sp.longitude.degrees,
                "alt_km": sp.elevation.km,
            },
        )

    return track


def initialize_satellites(
    parquet_path: str | Path = DEFAULT_PARQUET_PATH,
) -> Dict[str, EarthSatellite]:
    """Populate the global SATELLITES cache from the Parquet file."""
    global SATELLITES
    SATELLITES = load_satellites_from_parquet(parquet_path)
    return SATELLITES
