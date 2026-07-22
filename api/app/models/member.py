from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MembershipPlan(StrEnum):
    FREE = "free"
    PRO = "pro"


class MembershipStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    BANNED = "banned"


class UserContext(BaseModel):
    id: str
    email: str | None = None
    plan: MembershipPlan = MembershipPlan.FREE
    status: MembershipStatus = MembershipStatus.PENDING
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    ai_quota: int = 0
    backtest_quota: int = 0
    is_admin: bool = False
    demo: bool = False
    access_token: str = Field("", exclude=True)


class UsageSummary(BaseModel):
    plan: MembershipPlan
    status: MembershipStatus
    expires_at: datetime | None
    ai_used: int
    ai_limit: int
    backtests_used: int
    backtests_limit: int
    watchlist_used: int
    watchlist_limit: int


class WatchlistItem(BaseModel):
    symbol: str
    added_at: datetime


class WatchlistMutation(BaseModel):
    symbol: str
