from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Platania Quant API"
    cache_dir: Path = Path(os.getenv("PLATANIA_CACHE_DIR", ROOT_DIR / "data" / "cache"))
    cache_ttl_hours: int = int(os.getenv("PLATANIA_CACHE_TTL_HOURS", "24"))
    data_source: str = os.getenv("PLATANIA_DATA_SOURCE", "auto")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("PLATANIA_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )


settings = Settings()

