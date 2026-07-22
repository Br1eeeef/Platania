from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.app.core.auth import active_member
from api.app.data_sources import market_data_service
from api.app.data_sources.catalog import INSTRUMENTS
from api.app.indicators import add_indicators
from api.app.models.market import Bar, BarsResponse, DataKind
from api.app.models.strategy import SignalResponse, StrategyId
from api.app.strategies import get_strategy

router = APIRouter(tags=["market"], dependencies=[Depends(active_member)])


@router.get("/market/status")
def market_status() -> dict[str, object]:
    _, frame, meta = market_data_service.load("000300.SH")
    return {
        "market": "A股",
        "session": "closed",
        "latest_trade_date": frame.iloc[-1]["date"].date().isoformat(),
        "data_source": meta.provider,
        "data_kind": meta.kind,
        "updated_at": meta.updated_at,
        "is_stale": meta.is_stale,
        "future_markets": ["港股（即将支持）", "美股（即将支持）", "主流加密货币（即将支持）"],
    }


@router.get("/instruments")
def instruments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=30),
) -> dict[str, object]:
    values = [item for item in INSTRUMENTS.values() if item.sector != "宽基指数"]
    if search:
        keyword = search.strip().lower()
        values = [item for item in values if keyword in item.symbol.lower() or keyword in item.name.lower()]
    start = (page - 1) * page_size
    return {
        "items": values[start : start + page_size],
        "pagination": {"page": page, "page_size": page_size, "total": len(values)},
    }


@router.get("/market/{symbol}/bars", response_model=BarsResponse)
def bars(
    symbol: str,
    period: str = Query("1d", pattern="^(1d|1w)$"),
    limit: int = Query(260, ge=30, le=1000),
) -> BarsResponse:
    try:
        instrument, frame, meta = market_data_service.load(symbol)
        output = market_data_service.resample(frame, period).tail(limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    records = [Bar.model_validate({**row, "date": row["date"].date()}) for row in output.to_dict(orient="records")]
    return BarsResponse(instrument=instrument, period=period, bars=records, meta=meta)


@router.get("/market/{symbol}/indicators")
def indicators(symbol: str, limit: int = Query(260, ge=30, le=1000)) -> dict[str, object]:
    try:
        instrument, frame, meta = market_data_service.load(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = add_indicators(frame).tail(limit)
    columns = [
        "date",
        "ma5",
        "ma20",
        "ma60",
        "ma120",
        "ema12",
        "ema26",
        "macd",
        "macd_signal",
        "macd_hist",
        "rsi14",
        "bollinger_upper",
        "bollinger_lower",
        "atr14",
        "momentum60",
        "volume_ratio",
    ]
    history = data[columns].copy()
    history["date"] = history["date"].dt.date.astype(str)
    history = history.where(history.notna(), None)
    return {"instrument": instrument, "history": history.to_dict(orient="records"), "meta": meta}


@router.get("/market/{symbol}/signals", response_model=SignalResponse)
def signals(symbol: str, strategy_id: StrategyId = Query(StrategyId.TREND_MOMENTUM)) -> SignalResponse:
    try:
        instrument, frame, meta = market_data_service.load(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _, benchmark, _ = market_data_service.load("000300.SH")
    evaluation = get_strategy(strategy_id).evaluate(frame, benchmark)
    events = evaluation.frame[evaluation.frame["signal_event"].ne("")].tail(20)
    history = [
        {"date": row.date.date().isoformat(), "event": row.signal_event, "close": round(float(row.close), 3)}
        for row in events.itertuples()
    ]
    return SignalResponse(
        symbol=instrument.symbol,
        signal=evaluation.signal,
        history=history,
        data_source=meta.provider,
        is_demo=meta.kind == DataKind.DEMO,
    )


@router.post("/market/{symbol}/refresh")
def refresh(symbol: str, demo: bool = Query(False)) -> dict[str, object]:
    try:
        instrument, frame, meta = market_data_service.refresh(symbol, force_demo=demo)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"symbol": instrument.symbol, "bar_count": len(frame), "meta": meta}
