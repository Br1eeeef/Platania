from __future__ import annotations

from fastapi import APIRouter, Depends

from api.app.core.auth import active_member
from api.app.strategies import list_strategies

router = APIRouter(tags=["strategies"], dependencies=[Depends(active_member)])


@router.get("/strategies")
def strategies() -> dict[str, object]:
    return {"items": list_strategies(), "total": len(list_strategies())}
