from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator


class IndicatorName(StrEnum):
    CLOSE = "close"
    MA = "MA"
    EMA = "EMA"
    MACD = "MACD"
    RSI = "RSI"
    BOLLINGER_UPPER = "BollingerUpper"
    BOLLINGER_LOWER = "BollingerLower"
    ATR = "ATR"
    MOMENTUM = "momentum"
    VOLUME_RATIO = "volume_ratio"


class Operator(StrEnum):
    GT = "gt"
    LT = "lt"
    CROSS_ABOVE = "cross_above"
    CROSS_BELOW = "cross_below"


class IndicatorRef(BaseModel):
    name: IndicatorName
    period: int | None = Field(default=None, ge=2, le=250)

    @model_validator(mode="after")
    def period_matches_indicator(self) -> IndicatorRef:
        if self.name in {IndicatorName.CLOSE, IndicatorName.MACD} and self.period is not None:
            raise ValueError(f"{self.name} does not accept a period")
        if self.name not in {IndicatorName.CLOSE, IndicatorName.MACD} and self.period is None:
            raise ValueError(f"{self.name} requires a period")
        return self


class Condition(BaseModel):
    left: IndicatorRef
    operator: Operator
    right: IndicatorRef | float


class RiskRules(BaseModel):
    stop_loss_pct: float = Field(gt=0, le=0.2)
    take_profit_pct: float | None = Field(default=None, gt=0, le=1.0)
    max_position: float = Field(gt=0, le=0.5)


class CostRules(BaseModel):
    commission_rate: float = Field(0.0003, ge=0, le=0.01)
    stamp_duty_rate: float = Field(0.0005, ge=0, le=0.01)
    slippage_rate: float = Field(0.0005, ge=0, le=0.02)


class StrategySpec(BaseModel):
    version: Literal["1.0"] = "1.0"
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]
    market: Literal["A股"] = "A股"
    universe: list[str] = Field(default_factory=lambda: ["沪深A股"], min_length=1, max_length=20)
    exclusions: list[Literal["ST", "停牌", "上市不足120日"]] = Field(default_factory=lambda: ["ST", "停牌"])
    filters: list[Condition] = Field(default_factory=list, max_length=12)
    entry_conditions: list[Condition] = Field(min_length=1, max_length=12)
    exit_conditions: list[Condition] = Field(min_length=1, max_length=12)
    risk: RiskRules
    rebalance_frequency: Literal["daily", "weekly", "monthly"] = "daily"
    costs: CostRules = Field(default_factory=CostRules)
    benchmark: Literal["000300.SH", "000905.SH"] = "000300.SH"
    parameter_notes: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def complexity_guard(self) -> StrategySpec:
        total = len(self.filters) + len(self.entry_conditions) + len(self.exit_conditions)
        if total > 24:
            raise ValueError("strategy contains too many conditions")
        return self


class StrategyGenerationRequest(BaseModel):
    prompt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)]


class StrategyGenerationResponse(BaseModel):
    id: str
    mode: Literal["deepseek", "mock"]
    spec: StrategySpec
    readable_code: str
    input_tokens: int
    output_tokens: int
    daily_used: int
    daily_limit: int
    disclaimer: str
