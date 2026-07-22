from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.app.core.auth import active_member
from api.app.models.feed import FeedResponse
from api.app.services.feed import feed_service

router = APIRouter(tags=["feed"], dependencies=[Depends(active_member)])


@router.get("/feed", response_model=FeedResponse)
def feed(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50)) -> FeedResponse:
    return feed_service.list(page, page_size)
