from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class StrategyId(StrEnum):
    TREND_MOMENTUM = "trend_momentum"
    VOLUME_BREAKOUT = "volume_breakout"
    MEAN_REVERSION = "mean_reversion"


class SignalState(StrEnum):
    OBSERVE = "观察"
    CANDIDATE = "买入候选"
    HOLD = "持有"
    REDUCE = "减仓"
    EXIT = "退出"


class StrategyDescriptor(BaseModel):
    id: StrategyId
    name: str
    summary: str
    parameters: dict[str, float | int]


class SignalSnapshot(BaseModel):
    strategy_id: StrategyId
    state: SignalState
    generated_at: date
    reasons: list[str]
    invalidation: str
    risk_level: str
    score: float = Field(ge=0, le=100)
    values: dict[str, float | None]


class SignalResponse(BaseModel):
    symbol: str
    signal: SignalSnapshot
    history: list[dict[str, Any]]
    data_source: str
    is_demo: bool
