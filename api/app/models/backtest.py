from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .strategy import StrategyId


class BacktestRequest(BaseModel):
    symbol: str
    strategy_id: StrategyId
    initial_cash: float = Field(100_000, ge=10_000, le=100_000_000)
    commission_rate: float = Field(0.0003, ge=0, le=0.01)
    minimum_commission: float = Field(5, ge=0, le=100)
    stamp_duty_rate: float = Field(0.0005, ge=0, le=0.01)
    slippage_rate: float = Field(0.0005, ge=0, le=0.02)
    max_position: float = Field(0.9, gt=0, le=1)
    benchmark_symbol: str = Field("000300.SH", pattern=r"^[0-9]{6}\.(SH|SZ)$")
    start_date: date | None = None
    end_date: date | None = None
    strategy_parameters: dict[str, float | int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_configuration(self) -> BacktestRequest:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        rules: dict[StrategyId, dict[str, tuple[float, float]]] = {
            StrategyId.TREND_MOMENTUM: {"rsi_min": (0, 100), "rsi_max": (0, 100), "atr_stop": (0.5, 10)},
            StrategyId.VOLUME_BREAKOUT: {"volume_ratio": (0.5, 10), "atr_stop": (0.5, 10)},
            StrategyId.MEAN_REVERSION: {
                "rsi_entry": (1, 50),
                "rsi_exit": (30, 99),
                "max_holding_days": (1, 120),
            },
        }
        allowed = rules[self.strategy_id]
        unknown = set(self.strategy_parameters) - set(allowed)
        if unknown:
            raise ValueError(f"unsupported strategy parameters: {sorted(unknown)}")
        for name, value in self.strategy_parameters.items():
            lower, upper = allowed[name]
            if not lower <= float(value) <= upper:
                raise ValueError(f"{name} must be between {lower} and {upper}")
        if self.strategy_id == StrategyId.TREND_MOMENTUM:
            minimum = float(self.strategy_parameters.get("rsi_min", 42))
            maximum = float(self.strategy_parameters.get("rsi_max", 72))
            if minimum >= maximum:
                raise ValueError("rsi_min must be lower than rsi_max")
        if self.strategy_id == StrategyId.MEAN_REVERSION:
            entry = float(self.strategy_parameters.get("rsi_entry", 32))
            exit_value = float(self.strategy_parameters.get("rsi_exit", 55))
            if entry >= exit_value:
                raise ValueError("rsi_entry must be lower than rsi_exit")
        return self


class Trade(BaseModel):
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    quantity: int
    holding_days: int
    pnl: float
    return_rate: float
    costs: float


class BacktestMetrics(BaseModel):
    total_return: float
    annualized_return: float
    benchmark_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float | None
    trade_count: int
    average_holding_days: float


class BacktestResult(BaseModel):
    id: str
    symbol: str
    strategy_id: StrategyId | Literal["ai_generated"]
    status: str = "completed"
    metrics: BacktestMetrics
    equity_curve: list[dict[str, float | str]]
    drawdown_curve: list[dict[str, float | str]]
    trades: list[Trade]
    parameters: dict[str, Any]
    data_range: dict[str, str]
    data_source: str
    is_demo: bool
