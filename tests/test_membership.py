from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)


def invite_payload() -> dict[str, object]:
    now = datetime.now(UTC)
    return {
        "email": "member-test@example.com",
        "plan": "pro",
        "starts_at": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
        "ai_quota": 12,
        "backtest_quota": 34,
        "payment_confirmed": True,
        "payment_note": "测试环境线下付款确认",
        "external_payment_reference": "TEST-REFERENCE",
    }


def test_admin_invite_requires_confirmed_manual_payment() -> None:
    payload = invite_payload()
    payload["payment_confirmed"] = False
    response = client.post("/api/admin/members", json=payload)
    assert response.status_code == 422


def test_admin_membership_lifecycle_and_audit_log() -> None:
    invited = client.post("/api/admin/members", json=invite_payload())
    assert invited.status_code == 201
    member = invited.json()
    assert member["status"] == "active"
    assert member["email"] == "member-test@example.com"
    user_id = member["user_id"]

    suspended = client.patch(f"/api/admin/members/{user_id}", json={"action": "suspend"})
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"

    resumed = client.patch(f"/api/admin/members/{user_id}", json={"action": "resume"})
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "active"

    adjusted = client.patch(
        f"/api/admin/members/{user_id}",
        json={"action": "adjust_quota", "ai_quota": 21, "backtest_quota": 55},
    )
    assert adjusted.status_code == 200
    assert adjusted.json()["ai_quota"] == 21
    assert adjusted.json()["backtest_quota"] == 55

    banned = client.patch(f"/api/admin/members/{user_id}", json={"action": "ban"})
    assert banned.status_code == 200
    assert banned.json()["status"] == "banned"

    audit = client.get("/api/admin/audit-log")
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json() if item["target_user_id"] == user_id]
    assert {"invite", "suspend", "resume", "adjust_quota", "ban"}.issubset(actions)


def test_database_enforces_membership_and_feature_quotas() -> None:
    migration = Path("supabase/migrations/202607220001_initial_schema.sql").read_text(encoding="utf-8")
    assert "current_user_has_active_membership" in migration
    assert "as restrictive for all to authenticated" in migration
    assert "create trigger ai_usage_quota" in migration
    assert "create trigger backtest_runs_quota" in migration
    assert "member.status <> 'active'" in migration
