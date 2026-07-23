from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.app.models.member import MembershipPlan, MembershipStatus, UserContext

from .config import settings

bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> UserContext:
    if not settings.supabase_enabled:
        if settings.environment == "production":
            raise HTTPException(status_code=503, detail="生产环境尚未配置会员认证")
        now = datetime.now(UTC)
        return UserContext(
            id="demo-user",
            email="demo@platania.local",
            plan=MembershipPlan.PRO,
            status=MembershipStatus.ACTIVE,
            starts_at=now,
            expires_at=now + timedelta(days=365),
            ai_quota=50,
            backtest_quota=200,
            is_admin=True,
            demo=True,
        )
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    token = credentials.credentials
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_secret_key,
        "User-Agent": "Platania-API/0.2",
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(10, connect=5)) as client:
            response = client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/user", headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="会员认证服务暂时不可用") from exc
    if response.status_code in {401, 403}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录会话无效或已过期")
    try:
        response.raise_for_status()
        payload = response.json()
        user_id = str(payload["id"])
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="会员认证服务响应异常") from exc
    return UserContext(id=user_id, email=payload.get("email"), access_token=token)


def active_member(user: UserContext = Depends(current_user)) -> UserContext:
    from api.app.services.members import MembershipAccessError, member_service

    try:
        resolved = member_service.resolve_access(user)
    except MembershipAccessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return resolved


def admin_user(user: UserContext = Depends(active_member)) -> UserContext:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
