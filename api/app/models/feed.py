from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FeedKind(StrEnum):
    SIGNAL = "signal"
    RESEARCH = "research"
    BACKTEST = "backtest"
    STRATEGY_UPDATE = "strategy_update"


class FeedItem(BaseModel):
    id: str
    kind: FeedKind
    author_name: str
    title: str
    excerpt: str
    symbol: str | None = None
    strategy_id: str | None = None
    created_at: datetime
    likes: int = 0
    comments: int = 0
    is_demo: bool = False


class FeedResponse(BaseModel):
    items: list[FeedItem]
    page: int
    page_size: int
    total: int
    is_demo: bool


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    content: str = Field(min_length=20, max_length=20_000)
    symbol: str | None = None
    backtest_id: str | None = None
    is_public: bool = True
