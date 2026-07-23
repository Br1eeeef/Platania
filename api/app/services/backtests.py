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
        _, benchmark, _ = market_data_service.load(request.benchmark_symbol)
        strategy_parameters = {**request.strategy_parameters, "max_position": request.max_position}
        evaluation = get_strategy(request.strategy_id).evaluate(frame, benchmark, strategy_parameters)
        evaluated_frame = evaluation.frame
        if request.start_date:
            evaluated_frame = evaluated_frame[evaluated_frame["date"].dt.date >= request.start_date]
        if request.end_date:
            evaluated_frame = evaluated_frame[evaluated_frame["date"].dt.date <= request.end_date]
        if len(evaluated_frame) < 130:
            raise ValueError("selected date range must contain at least 130 trading bars")
        result = self.engine.run(
            evaluated_frame,
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
