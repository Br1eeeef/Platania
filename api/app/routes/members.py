from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.app.core.auth import active_member
from api.app.data_sources.catalog import get_instrument
from api.app.models.member import UserContext, WatchlistItem, WatchlistMutation
from api.app.services.members import UsageExceeded, member_service

router = APIRouter(tags=["members"])


@router.get("/me")
def me(user: UserContext = Depends(active_member)) -> dict[str, object]:
    return {"user": user, "usage": member_service.summary(user), "mode": "demo" if user.demo else "supabase"}


@router.get("/watchlist", response_model=list[WatchlistItem])
def watchlist(user: UserContext = Depends(active_member)) -> list[WatchlistItem]:
    return member_service.list_watchlist(user)


@router.post("/watchlist", response_model=WatchlistItem, status_code=201)
def add_watchlist(request: WatchlistMutation, user: UserContext = Depends(active_member)) -> WatchlistItem:
    try:
        symbol = get_instrument(request.symbol).symbol
        return member_service.add_watchlist(user, symbol)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UsageExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.delete("/watchlist/{symbol}", status_code=204)
def remove_watchlist(symbol: str, user: UserContext = Depends(active_member)) -> Response:
    member_service.remove_watchlist(user, get_instrument(symbol).symbol)
    return Response(status_code=204)
