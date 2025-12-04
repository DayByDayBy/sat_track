from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and optional .env.

    Env vars are prefixed with SAT_TRACK_, e.g. SAT_TRACK_TLE_URL.
    """

    model_config = SettingsConfigDict(env_prefix="SAT_TRACK_", env_file=".env", extra="ignore")

    # TLE / data
    tle_url: str = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=raw"
    parquet_path: Path = Path("data/tles.parquet")

    # Scheduler / WS timing
    scheduler_interval_seconds: float = 5.0
    ws_interval_seconds: float = 5.0
    ws_max_sats: int = 500

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: Any) -> Any:
        """Allow comma-separated string in SAT_TRACK_CORS_ORIGINS env var."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
