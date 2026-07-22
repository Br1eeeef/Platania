from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.app.core.auth import active_member
from api.app.models.backtest import BacktestRequest, BacktestResult
from api.app.models.member import UserContext
from api.app.services.backtests import backtest_service
from api.app.services.members import UsageExceeded, member_service

router = APIRouter(tags=["backtests"])


@router.post("/backtests", response_model=BacktestResult, status_code=201)
def create_backtest(request: BacktestRequest, user: UserContext = Depends(active_member)) -> BacktestResult:
    try:
        member_service.assert_available(user, "backtests")
        result = backtest_service.create(request)
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


@router.get("/backtests/{result_id}", response_model=BacktestResult)
def get_backtest(result_id: str, user: UserContext = Depends(active_member)) -> BacktestResult:
    del user
    result = backtest_service.get(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="回测记录不存在或已过期")
    return result
