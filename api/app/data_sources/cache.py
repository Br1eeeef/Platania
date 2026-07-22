from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from api.app.models.market import DataMeta

from .base import validate_frame


class ParquetCache:
    def __init__(self, root: Path, ttl_hours: int) -> None:
        self.root = root
        self.ttl = timedelta(hours=ttl_hours)
        self.root.mkdir(parents=True, exist_ok=True)

    def read(self, symbol: str) -> tuple[pd.DataFrame, DataMeta] | None:
        bars_path, meta_path = self._paths(symbol)
        if not bars_path.exists() or not meta_path.exists():
            return None
        try:
            frame = validate_frame(pd.read_parquet(bars_path))
            meta = DataMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
            meta.is_stale = datetime.now(UTC) - meta.updated_at.astimezone(UTC) > self.ttl
            return frame, meta
        except (OSError, ValueError, json.JSONDecodeError):
            return None

    def write(self, symbol: str, frame: pd.DataFrame, meta: DataMeta) -> None:
        normalized = validate_frame(frame)
        bars_path, meta_path = self._paths(symbol)
        bars_tmp = bars_path.with_suffix(".tmp.parquet")
        meta_tmp = meta_path.with_suffix(".tmp.json")
        normalized.to_parquet(bars_tmp, index=False)
        meta_tmp.write_text(meta.model_dump_json(indent=2), encoding="utf-8")
        bars_tmp.replace(bars_path)
        meta_tmp.replace(meta_path)

    def merge(self, symbol: str, new_frame: pd.DataFrame, meta: DataMeta) -> pd.DataFrame:
        existing = self.read(symbol)
        combined = pd.concat([existing[0], new_frame], ignore_index=True) if existing else new_frame
        combined = validate_frame(combined)
        self.write(symbol, combined, meta)
        return combined

    def _paths(self, symbol: str) -> tuple[Path, Path]:
        slug = symbol.lower().replace(".", "_")
        return self.root / f"{slug}.parquet", self.root / f"{slug}.meta.json"
