from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from api.app.models.strategy import SignalSnapshot, StrategyDescriptor


@dataclass(frozen=True)
class StrategyEvaluation:
    frame: pd.DataFrame
    signal: SignalSnapshot


class Strategy(ABC):
    descriptor: StrategyDescriptor

    @abstractmethod
    def evaluate(
        self,
        frame: pd.DataFrame,
        benchmark: pd.DataFrame | None = None,
        parameters: dict[str, float | int] | None = None,
    ) -> StrategyEvaluation:
        """Return close-time target positions. Execution is deferred by the backtester."""


def risk_level(atr_ratio: float) -> str:
    if atr_ratio >= 0.04:
        return "高"
    if atr_ratio >= 0.025:
        return "中"
    return "低"


def safe_value(value: object) -> float | None:
    try:
        numeric = float(value)
        return None if pd.isna(numeric) else round(numeric, 4)
    except (TypeError, ValueError):
        return None
