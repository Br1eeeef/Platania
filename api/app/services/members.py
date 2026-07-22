from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime

import httpx

from api.app.core.config import settings
from api.app.models.member import MembershipPlan, MembershipStatus, UsageSummary, UserContext, WatchlistItem

WATCHLIST_LIMITS = {MembershipPlan.FREE: 10, MembershipPlan.PRO: 100}


class UsageExceeded(RuntimeError):
    pass


class MembershipAccessError(RuntimeError):
    def __init__(self, message: str, status_code: int = 403) -> None:
        super().__init__(message)
        self.status_code = status_code


class MemberService:
    def __init__(self) -> None:
        self.usage: dict[tuple[str, date, str], int] = defaultdict(int)
        self.demo_watchlists: dict[str, dict[str, WatchlistItem]] = defaultdict(dict)

    def resolve_access(self, user: UserContext) -> UserContext:
        if user.demo:
            return user
        if settings.environment == "production" and not settings.supabase_secret_key:
            raise MembershipAccessError("服务器尚未配置 Supabase Secret Key", 503)
        response = self._supabase_request(
            user,
            "GET",
            "/rest/v1/memberships",
            params={"select": "plan,status,starts_at,expires_at,ai_quota,backtest_quota", "user_id": f"eq.{user.id}"},
        )
        rows = response.json()
        if not rows:
            raise MembershipAccessError("账号尚未由管理员开通会员")
        membership = rows[0]
        now = datetime.now(UTC)
        starts_at = datetime.fromisoformat(membership["starts_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(membership["expires_at"].replace("Z", "+00:00"))
        membership_status = MembershipStatus(membership["status"])
        if membership_status == MembershipStatus.BANNED:
            raise MembershipAccessError("账号已被封禁")
        if membership_status == MembershipStatus.SUSPENDED:
            raise MembershipAccessError("会员已暂停，请联系 Br1ef")
        if membership_status != MembershipStatus.ACTIVE:
            raise MembershipAccessError("会员尚未激活或已失效")
        if starts_at > now:
            raise MembershipAccessError("会员尚未到开始时间")
        if expires_at <= now:
            raise MembershipAccessError("会员已到期，请联系 Br1ef 续费")
        profile = self._supabase_request(
            user, "GET", "/rest/v1/profiles", params={"select": "is_admin", "id": f"eq.{user.id}"}
        ).json()
        return user.model_copy(
            update={
                "plan": MembershipPlan(membership["plan"]),
                "status": membership_status,
                "starts_at": starts_at,
                "expires_at": expires_at,
                "ai_quota": int(membership["ai_quota"]),
                "backtest_quota": int(membership["backtest_quota"]),
                "is_admin": user.id in settings.admin_user_ids or bool(profile and profile[0].get("is_admin")),
            }
        )

    def summary(self, user: UserContext) -> UsageSummary:
        ai_used, backtests_used = self._usage_counts(user)
        return UsageSummary(
            plan=user.plan,
            status=user.status,
            expires_at=user.expires_at,
            ai_used=ai_used,
            ai_limit=user.ai_quota,
            backtests_used=backtests_used,
            backtests_limit=user.backtest_quota,
            watchlist_used=len(self.list_watchlist(user)),
            watchlist_limit=WATCHLIST_LIMITS[user.plan],
        )

    def assert_available(self, user: UserContext, kind: str) -> None:
        ai_used, backtests_used = self._usage_counts(user)
        used = ai_used if kind == "ai" else backtests_used
        limit = user.ai_quota if kind == "ai" else user.backtest_quota
        if used >= limit:
            raise UsageExceeded(f"今日 {kind} 额度已用完")

    def record(self, user: UserContext, kind: str, metadata: dict[str, object] | None = None) -> None:
        metadata = metadata or {}
        if user.demo or not settings.supabase_secret_key:
            self.usage[(user.id, date.today(), kind)] += 1
            return
        if kind == "ai":
            self._admin_request(
                "POST",
                "/rest/v1/ai_usage",
                json={
                    "user_id": user.id,
                    "request_id": str(uuid.uuid4()),
                    "status": "completed",
                    "input_tokens": metadata.get("input_tokens", 0),
                    "output_tokens": metadata.get("output_tokens", 0),
                    "model": metadata.get("model", "unknown"),
                },
            )
        else:
            self._admin_request(
                "POST",
                "/rest/v1/backtest_runs",
                json={
                    "id": metadata.get("id", str(uuid.uuid4())),
                    "user_id": user.id,
                    "symbol": metadata.get("symbol", "unknown"),
                    "status": "completed",
                    "parameters": metadata.get("parameters", {}),
                    "metrics": metadata.get("metrics", {}),
                    "data_source": metadata.get("data_source"),
                    "is_demo": metadata.get("is_demo", False),
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )

    def list_watchlist(self, user: UserContext) -> list[WatchlistItem]:
        if user.demo:
            return list(self.demo_watchlists[user.id].values())
        response = self._supabase_request(
            user, "GET", "/rest/v1/watchlist_items", params={"select": "symbol,added_at", "user_id": f"eq.{user.id}"}
        )
        return [WatchlistItem.model_validate(item) for item in response.json()]

    def add_watchlist(self, user: UserContext, symbol: str) -> WatchlistItem:
        existing = self.list_watchlist(user)
        if symbol not in {item.symbol for item in existing} and len(existing) >= WATCHLIST_LIMITS[user.plan]:
            raise UsageExceeded("自选股数量已达到会员上限")
        item = WatchlistItem(symbol=symbol, added_at=datetime.now(UTC))
        if user.demo:
            self.demo_watchlists[user.id][symbol] = item
            return item
        response = self._supabase_request(
            user,
            "POST",
            "/rest/v1/watchlist_items",
            json={"user_id": user.id, **item.model_dump(mode="json")},
            headers={"Prefer": "return=representation,resolution=merge-duplicates"},
        )
        return WatchlistItem.model_validate(response.json()[0])

    def remove_watchlist(self, user: UserContext, symbol: str) -> None:
        if user.demo:
            self.demo_watchlists[user.id].pop(symbol, None)
            return
        self._supabase_request(
            user, "DELETE", "/rest/v1/watchlist_items", params={"user_id": f"eq.{user.id}", "symbol": f"eq.{symbol}"}
        )

    def _usage_counts(self, user: UserContext) -> tuple[int, int]:
        if user.demo or not settings.supabase_secret_key:
            return self.usage[(user.id, date.today(), "ai")], self.usage[(user.id, date.today(), "backtests")]
        today = date.today().isoformat()
        ai = self._admin_request(
            "GET",
            "/rest/v1/ai_usage",
            params={"select": "id", "user_id": f"eq.{user.id}", "usage_date": f"eq.{today}", "status": "eq.completed"},
        ).json()
        start = f"{today}T00:00:00Z"
        backtests = self._admin_request(
            "GET",
            "/rest/v1/backtest_runs",
            params={"select": "id", "user_id": f"eq.{user.id}", "created_at": f"gte.{start}", "status": "eq.completed"},
        ).json()
        return len(ai), len(backtests)

    @staticmethod
    def _supabase_request(user: UserContext, method: str, path: str, **kwargs: object) -> httpx.Response:
        if not settings.supabase_secret_key:
            raise MembershipAccessError("Supabase Secret Key 未配置", 503)
        headers = {"Authorization": f"Bearer {user.access_token}", "apikey": settings.supabase_secret_key}
        headers.update(kwargs.pop("headers", {}))
        with httpx.Client(timeout=httpx.Timeout(12, connect=5)) as client:
            response = client.request(method, f"{settings.supabase_url.rstrip('/')}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            return response

    @staticmethod
    def _admin_request(method: str, path: str, **kwargs: object) -> httpx.Response:
        if not settings.supabase_secret_key:
            raise MembershipAccessError("Supabase Secret Key 未配置", 503)
        headers = {"Authorization": f"Bearer {settings.supabase_secret_key}", "apikey": settings.supabase_secret_key}
        headers.update(kwargs.pop("headers", {}))
        with httpx.Client(timeout=httpx.Timeout(15, connect=5)) as client:
            response = client.request(method, f"{settings.supabase_url.rstrip('/')}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            return response


member_service = MemberService()
