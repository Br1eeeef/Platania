from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from .member import MembershipPlan, MembershipStatus


class MemberInviteRequest(BaseModel):
    email: EmailStr
    plan: MembershipPlan
    starts_at: datetime
    expires_at: datetime
    ai_quota: int = Field(ge=0, le=10000)
    backtest_quota: int = Field(ge=0, le=10000)
    payment_confirmed: bool
    payment_note: str = Field("", max_length=500)
    external_payment_reference: str = Field("", max_length=120)

    @model_validator(mode="after")
    def validate_membership(self) -> MemberInviteRequest:
        if self.expires_at <= self.starts_at:
            raise ValueError("到期时间必须晚于开始时间")
        if not self.payment_confirmed:
            raise ValueError("管理员必须先确认线下付款")
        return self


class MemberUpdateRequest(BaseModel):
    action: str = Field(pattern="^(renew|suspend|resume|ban|adjust_quota)$")
    expires_at: datetime | None = None
    ai_quota: int | None = Field(default=None, ge=0, le=10000)
    backtest_quota: int | None = Field(default=None, ge=0, le=10000)
    payment_note: str | None = Field(default=None, max_length=500)
    external_payment_reference: str | None = Field(default=None, max_length=120)


class AdminMember(BaseModel):
    user_id: str
    email: str | None = None
    plan: MembershipPlan
    status: MembershipStatus
    starts_at: datetime
    expires_at: datetime
    ai_quota: int
    backtest_quota: int
    payment_note: str | None = None
    external_payment_reference: str | None = None
    created_at: datetime
    updated_at: datetime


class AuditLog(BaseModel):
    id: str
    admin_user_id: str
    target_user_id: str | None
    action: str
    before_state: dict[str, object] | None
    after_state: dict[str, object] | None
    metadata: dict[str, object]
    created_at: datetime
