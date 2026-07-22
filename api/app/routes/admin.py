from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response

from api.app.core.auth import admin_user
from api.app.models.admin import AdminMember, AuditLog, MemberInviteRequest, MemberUpdateRequest
from api.app.models.member import UserContext
from api.app.services.admin import admin_service

router = APIRouter(tags=["admin"], dependencies=[Depends(admin_user)])


@router.get("/admin")
def dashboard(admin: UserContext = Depends(admin_user)) -> dict[str, object]:
    members = admin_service.list_members(admin)
    now = datetime.now(UTC)
    return {
        "total": len(members),
        "active": sum(member.status == "active" and member.expires_at > now for member in members),
        "expiring_soon": sum(
            member.status == "active" and now < member.expires_at <= now + timedelta(days=14) for member in members
        ),
        "suspended": sum(member.status == "suspended" for member in members),
    }


@router.get("/admin/members", response_model=list[AdminMember])
def members(admin: UserContext = Depends(admin_user)) -> list[AdminMember]:
    return admin_service.list_members(admin)


@router.post("/admin/members", response_model=AdminMember, status_code=201)
def invite_member(request: MemberInviteRequest, admin: UserContext = Depends(admin_user)) -> AdminMember:
    try:
        return admin_service.invite(admin, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/admin/members/{user_id}", response_model=AdminMember)
def update_member(user_id: str, request: MemberUpdateRequest, admin: UserContext = Depends(admin_user)) -> AdminMember:
    try:
        return admin_service.update(admin, user_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="会员不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/admin/usage")
def usage(admin: UserContext = Depends(admin_user)) -> dict[str, object]:
    members = admin_service.list_members(admin)
    return {
        "members": [
            {
                "user_id": member.user_id,
                "email": member.email,
                "ai_quota": member.ai_quota,
                "backtest_quota": member.backtest_quota,
            }
            for member in members
        ]
    }


@router.get("/admin/audit-log", response_model=list[AuditLog])
def audit_log(admin: UserContext = Depends(admin_user)) -> list[AuditLog]:
    return admin_service.audit_logs(admin)


@router.get("/admin/members.csv")
def export_members(admin: UserContext = Depends(admin_user)) -> Response:
    return Response(
        content=admin_service.export_csv(admin),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=platania-members.csv"},
    )
