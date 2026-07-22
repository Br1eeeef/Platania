from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta

from api.app.core.config import settings
from api.app.models.admin import AdminMember, AuditLog, MemberInviteRequest, MemberUpdateRequest
from api.app.models.member import MembershipStatus, UserContext

from .members import member_service
from .payments import PaymentConfirmation, payment_provider


class AdminService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.demo_members: dict[str, AdminMember] = {
            "demo-user": AdminMember(
                user_id="demo-user",
                email="demo@platania.local",
                plan="pro",
                status="active",
                starts_at=now,
                expires_at=now + timedelta(days=365),
                ai_quota=50,
                backtest_quota=200,
                payment_note="演示会员，不是真实付款",
                external_payment_reference="DEMO",
                created_at=now,
                updated_at=now,
            )
        }
        self.demo_audit: list[AuditLog] = []

    def list_members(self, admin: UserContext) -> list[AdminMember]:
        if admin.demo:
            return list(self.demo_members.values())
        rows = member_service._admin_request(
            "GET", "/rest/v1/memberships", params={"select": "*", "order": "expires_at.asc"}
        ).json()
        return [AdminMember.model_validate(row) for row in rows]

    def invite(self, admin: UserContext, request: MemberInviteRequest) -> AdminMember:
        payment_provider.confirm(
            PaymentConfirmation(request.payment_confirmed, request.payment_note, request.external_payment_reference)
        )
        if admin.demo:
            user_id = f"demo-{len(self.demo_members) + 1}"
            now = datetime.now(UTC)
            member = AdminMember(
                user_id=user_id,
                email=str(request.email),
                plan=request.plan,
                status="active",
                starts_at=request.starts_at,
                expires_at=request.expires_at,
                ai_quota=request.ai_quota,
                backtest_quota=request.backtest_quota,
                payment_note=request.payment_note,
                external_payment_reference=request.external_payment_reference,
                created_at=now,
                updated_at=now,
            )
            self.demo_members[user_id] = member
            self._audit(admin, user_id, "invite", None, member.model_dump(mode="json"))
            return member
        invite = member_service._admin_request(
            "POST",
            "/auth/v1/invite",
            params={"redirect_to": f"{settings.public_url.rstrip('/')}/auth/setup-password"},
            json={"email": str(request.email), "data": {"invited_by": admin.id}},
        ).json()
        user_id = invite["id"]
        payload = {
            "user_id": user_id,
            "plan": request.plan,
            "status": "active",
            "starts_at": request.starts_at.isoformat(),
            "expires_at": request.expires_at.isoformat(),
            "ai_quota": request.ai_quota,
            "backtest_quota": request.backtest_quota,
            "payment_note": request.payment_note,
            "external_payment_reference": request.external_payment_reference,
            "created_by": admin.id,
        }
        response = member_service._admin_request(
            "POST", "/rest/v1/memberships", json=payload, headers={"Prefer": "return=representation,resolution=merge-duplicates"}
        )
        member = AdminMember.model_validate({**response.json()[0], "email": str(request.email)})
        self._audit(admin, user_id, "invite", None, member.model_dump(mode="json"))
        return member

    def update(self, admin: UserContext, user_id: str, request: MemberUpdateRequest) -> AdminMember:
        before = next((member for member in self.list_members(admin) if member.user_id == user_id), None)
        if before is None:
            raise KeyError(user_id)
        changes: dict[str, object] = {}
        if request.action == "renew":
            if request.expires_at is None or request.expires_at <= before.expires_at:
                raise ValueError("续费后的到期时间必须晚于当前到期时间")
            payment_provider.confirm(
                PaymentConfirmation(True, request.payment_note or "", request.external_payment_reference or "")
            )
            changes = {
                "expires_at": request.expires_at,
                "status": MembershipStatus.ACTIVE,
                "payment_note": request.payment_note,
                "external_payment_reference": request.external_payment_reference,
            }
        elif request.action == "suspend":
            changes = {"status": MembershipStatus.SUSPENDED}
        elif request.action == "resume":
            changes = {"status": MembershipStatus.ACTIVE}
        elif request.action == "ban":
            changes = {"status": MembershipStatus.BANNED}
        elif request.action == "adjust_quota":
            if request.ai_quota is None and request.backtest_quota is None:
                raise ValueError("至少调整一项额度")
            if request.ai_quota is not None:
                changes["ai_quota"] = request.ai_quota
            if request.backtest_quota is not None:
                changes["backtest_quota"] = request.backtest_quota
        changes["updated_at"] = datetime.now(UTC)
        if admin.demo:
            after = before.model_copy(update=changes)
            self.demo_members[user_id] = after
        else:
            response = member_service._admin_request(
                "PATCH",
                "/rest/v1/memberships",
                params={"user_id": f"eq.{user_id}"},
                json={key: value.isoformat() if isinstance(value, datetime) else value for key, value in changes.items()},
                headers={"Prefer": "return=representation"},
            )
            after = AdminMember.model_validate(response.json()[0])
        self._audit(admin, user_id, request.action, before.model_dump(mode="json"), after.model_dump(mode="json"))
        return after

    def audit_logs(self, admin: UserContext) -> list[AuditLog]:
        if admin.demo:
            return list(reversed(self.demo_audit))
        rows = member_service._admin_request(
            "GET", "/rest/v1/admin_audit_logs", params={"select": "*", "order": "created_at.desc", "limit": "200"}
        ).json()
        return [AuditLog.model_validate(row) for row in rows]

    def export_csv(self, admin: UserContext) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "user_id",
                "email",
                "plan",
                "status",
                "starts_at",
                "expires_at",
                "ai_quota",
                "backtest_quota",
                "external_payment_reference",
            ]
        )
        for member in self.list_members(admin):
            writer.writerow(
                [
                    member.user_id,
                    member.email or "",
                    member.plan,
                    member.status,
                    member.starts_at.isoformat(),
                    member.expires_at.isoformat(),
                    member.ai_quota,
                    member.backtest_quota,
                    member.external_payment_reference or "",
                ]
            )
        return output.getvalue()

    def _audit(
        self,
        admin: UserContext,
        target: str | None,
        action: str,
        before: dict[str, object] | None,
        after: dict[str, object] | None,
    ) -> None:
        payload = {
            "admin_user_id": admin.id,
            "target_user_id": target,
            "action": action,
            "before_state": before,
            "after_state": after,
            "metadata": {},
        }
        if admin.demo:
            self.demo_audit.append(AuditLog(id=f"audit-{len(self.demo_audit) + 1}", created_at=datetime.now(UTC), **payload))
        else:
            member_service._admin_request("POST", "/rest/v1/admin_audit_logs", json=payload)


admin_service = AdminService()
