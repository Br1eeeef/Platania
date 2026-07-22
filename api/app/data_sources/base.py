from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from api.app.models.market import Instrument

STANDARD_COLUMNS = ["date", "open", "high", "low", "close", "volume", "amount", "suspended", "adjustment"]


class ProviderError(RuntimeError):
    pass


class ProviderUnavailable(ProviderError):
    pass


class MarketDataProvider(ABC):
    name: str
    live: bool = True

    @abstractmethod
    def fetch_daily(self, instrument: Instrument, start: date, end: date, adjustment: str = "qfq") -> pd.DataFrame:
        """Return normalized daily bars without provider-specific column names."""


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(STANDARD_COLUMNS) - set(frame.columns)
    if missing:
        raise ProviderError(f"missing normalized fields: {sorted(missing)}")
    normalized = frame[STANDARD_COLUMNS].copy()
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce").dt.normalize()
    numeric = ["open", "high", "low", "close", "volume", "amount"]
    normalized[numeric] = normalized[numeric].apply(pd.to_numeric, errors="coerce")
    normalized = normalized.dropna(subset=["date", "open", "high", "low", "close"])
    normalized = normalized.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    invalid = (
        (normalized["low"] > normalized["high"])
        | (normalized["high"] < normalized[["open", "close"]].max(axis=1))
        | (normalized["low"] > normalized[["open", "close"]].min(axis=1))
        | (normalized[["open", "high", "low", "close"]] <= 0).any(axis=1)
    )
    if invalid.any():
        raise ProviderError(f"invalid OHLC rows: {int(invalid.sum())}")
    return normalized
