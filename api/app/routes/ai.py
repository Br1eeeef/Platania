from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.app.ai.compiler import compile_readable_code, evaluate_spec
from api.app.ai.service import QuotaExceeded, ai_strategy_service
from api.app.ai.spec import StrategyGenerationRequest, StrategyGenerationResponse, StrategySpec
from api.app.backtest import BacktestEngine
from api.app.core.auth import active_member
from api.app.data_sources import market_data_service
from api.app.models.backtest import BacktestRequest, BacktestResult
from api.app.models.member import UserContext
from api.app.services.members import UsageExceeded, member_service

router = APIRouter(tags=["ai"])


class AiBacktestRequest(BaseModel):
    symbol: str
    spec: StrategySpec
    initial_cash: float = 100_000


@router.post("/ai/strategy", response_model=StrategyGenerationResponse, status_code=201)
def generate_strategy(
    request: StrategyGenerationRequest, user: UserContext = Depends(active_member)
) -> StrategyGenerationResponse:
    try:
        member_service.assert_available(user, "ai")
        result = ai_strategy_service.generate(user.id, request.prompt, user.ai_quota)
        try:
            member_service.record(
                user, "ai", {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens, "model": result.mode}
            )
        except Exception:
            ai_strategy_service.refund(user.id, result.id)
            raise
        return result
    except (UsageExceeded, QuotaExceeded) as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.post("/ai/strategy/validate")
def validate_strategy(spec: StrategySpec, user: UserContext = Depends(active_member)) -> dict[str, object]:
    del user
    return {"valid": True, "spec": spec, "readable_code": compile_readable_code(spec)}


@router.post("/ai/strategy/backtest", response_model=BacktestResult, status_code=201)
def backtest_strategy(request: AiBacktestRequest, user: UserContext = Depends(active_member)) -> BacktestResult:
    try:
        member_service.assert_available(user, "backtests")
        instrument, frame, meta = market_data_service.load(request.symbol)
        _, benchmark, _ = market_data_service.load(request.spec.benchmark)
        evaluated = evaluate_spec(frame, request.spec)
        standard_request = BacktestRequest(
            symbol=instrument.symbol,
            strategy_id="trend_momentum",
            initial_cash=request.initial_cash,
            commission_rate=request.spec.costs.commission_rate,
            stamp_duty_rate=request.spec.costs.stamp_duty_rate,
            slippage_rate=request.spec.costs.slippage_rate,
            max_position=request.spec.risk.max_position,
        )
        result = BacktestEngine().run(
            evaluated, benchmark, standard_request, provider=meta.provider, is_demo=meta.kind.value == "demo"
        )
        result = BacktestResult.model_validate({**result.model_dump(), "strategy_id": "ai_generated"})
        result.parameters["ai_strategy_name"] = request.spec.name
        member_service.record(
            user,
            "backtests",
            {
                "id": result.id,
                "symbol": result.symbol,
                "parameters": result.parameters,
                "metrics": result.metrics.model_dump(),
                "data_source": result.data_source,
                "is_demo": result.is_demo,
            },
        )
        return result
    except UsageExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
