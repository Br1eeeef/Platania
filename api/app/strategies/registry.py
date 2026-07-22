from __future__ import annotations

from api.app.models.strategy import StrategyDescriptor, StrategyId

from .base import Strategy
from .mean_reversion import MeanReversionStrategy
from .trend_momentum import TrendMomentumStrategy
from .volume_breakout import VolumeBreakoutStrategy

_STRATEGIES: dict[StrategyId, Strategy] = {
    StrategyId.TREND_MOMENTUM: TrendMomentumStrategy(),
    StrategyId.VOLUME_BREAKOUT: VolumeBreakoutStrategy(),
    StrategyId.MEAN_REVERSION: MeanReversionStrategy(),
}


def get_strategy(strategy_id: StrategyId | str) -> Strategy:
    return _STRATEGIES[StrategyId(strategy_id)]


def list_strategies() -> list[StrategyDescriptor]:
    return [strategy.descriptor for strategy in _STRATEGIES.values()]
