from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataKind(StrEnum):
    LIVE = "live"
    DEMO = "demo"


class Instrument(BaseModel):
    symbol: str
    code: str
    name: str
    exchange: str
    market: str = "A股"
    sector: str
    status: str = "active"


class Bar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    amount: float = Field(ge=0)
    suspended: bool = False
    adjustment: str = "qfq"

    @model_validator(mode="after")
    def validate_ohlc(self) -> Bar:
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLC range")
        if self.low > self.high:
            raise ValueError("low cannot exceed high")
        return self


class DataMeta(BaseModel):
    provider: str
    kind: DataKind
    updated_at: datetime
    adjustment: str = "qfq"
    is_stale: bool = False
    warnings: list[str] = Field(default_factory=list)


class BarsResponse(BaseModel):
    instrument: Instrument
    period: str
    bars: list[Bar]
    meta: DataMeta
