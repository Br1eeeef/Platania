from __future__ import annotations

from collections import OrderedDict

from api.app.backtest import BacktestEngine
from api.app.data_sources import market_data_service
from api.app.models.backtest import BacktestRequest, BacktestResult
from api.app.models.market import DataKind
from api.app.strategies import get_strategy


class BacktestService:
    def __init__(self, capacity: int = 100) -> None:
        self.capacity = capacity
        self.results: OrderedDict[str, BacktestResult] = OrderedDict()
        self.engine = BacktestEngine()

    def create(self, request: BacktestRequest) -> BacktestResult:
        _, frame, meta = market_data_service.load(request.symbol)
        _, benchmark, _ = market_data_service.load("000300.SH")
        evaluation = get_strategy(request.strategy_id).evaluate(frame, benchmark)
        result = self.engine.run(
            evaluation.frame,
            benchmark,
            request,
            provider=meta.provider,
            is_demo=meta.kind == DataKind.DEMO,
        )
        self.results[result.id] = result
        while len(self.results) > self.capacity:
            self.results.popitem(last=False)
        return result

    def get(self, result_id: str) -> BacktestResult | None:
        return self.results.get(result_id)


backtest_service = BacktestService()
