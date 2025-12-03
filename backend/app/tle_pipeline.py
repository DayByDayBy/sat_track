from __future__ import annotations

import argparse
import logging
import urllib.request
from pathlib import Path
from typing import List, Dict, Tuple

import polars as pl
from skyfield.api import EarthSatellite, load


LOGGER = logging.getLogger(__name__)
TS = load.timescale()

DEFAULT_TLE_URL = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=raw"
)
DEFAULT_PARQUET_PATH = Path("data/tles.parquet")


def fetch_and_parse_raw_tles(url: str) -> Tuple[List[EarthSatellite], List[Dict[str, str]]]:
    """Fetch raw TLE text, parse into EarthSatellite objects, and return raw rows."""
    
    # Fetch the raw TLE text:
    with urllib.request.urlopen(url) as f:
        text = f.read().decode('utf-8')

    lines = text.strip().splitlines()
    raw_rows: List[Dict[str, str]] = []

    i = 0
    while i < len(lines):
        name = lines[i].strip()
        if i + 2 >= len(lines):
            break
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()

        # Sanity check
        if line1.startswith("1 ") and line2.startswith("2 "):
            raw_rows.append({"name": name, "line1": line1, "line2": line2})
        i += 3

    # Build EarthSatellite objects directly from raw_rows
    satellites = [
        EarthSatellite(row["line1"], row["line2"], row["name"], TS)
        for row in raw_rows
    ]

    LOGGER.info("Parsed %d satellites from %s", len(satellites), url)
    return satellites, raw_rows


def load_and_store_tles(
    url: str = DEFAULT_TLE_URL,
    parquet_path: str | Path = DEFAULT_PARQUET_PATH,
) -> Path:
    """High-level wrapper: fetch TLEs and store them."""
    satellites, raw_rows = fetch_and_parse_raw_tles(url)
    
    if not raw_rows:
        msg = "No valid TLE rows were produced from satellites list"
        LOGGER.error(msg)
        raise RuntimeError(msg)

    df = pl.DataFrame(raw_rows)
    target = Path(parquet_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(target)

    LOGGER.info("Wrote %d TLEs to %s", len(raw_rows), target)
    return target


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch TLEs from Celestrak and store them in Parquet."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_TLE_URL,
        help=f"TLE source URL (default: {DEFAULT_TLE_URL})",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_PARQUET_PATH),
        help=f"Output Parquet path (default: {DEFAULT_PARQUET_PATH})",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    try:
        path = load_and_store_tles(args.url, args.out)
    except Exception:
        LOGGER.exception("Failed to fetch and store TLEs")
        raise
    else:
        LOGGER.info("Successfully stored TLEs at %s", path)


if __name__ == "__main__":
    main()
