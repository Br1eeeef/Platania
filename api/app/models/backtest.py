from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

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
    parameters: dict[str, float | int | str]
    data_range: dict[str, str]
    data_source: str
    is_demo: bool
