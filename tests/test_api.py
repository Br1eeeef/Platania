from __future__ import annotations

from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)


def test_health_reports_demo_integrations() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_mode"] in {"mock", "deepseek"}


def test_market_bars_are_explicitly_labeled() -> None:
    response = client.get("/api/market/600519.SH/bars?limit=120")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["bars"]) == 120
    assert payload["meta"]["kind"] in {"demo", "live"}
    assert payload["meta"]["provider"]


def test_ai_mock_and_validation_contract() -> None:
    response = client.post("/api/ai/strategy", json={"prompt": "生成A股趋势策略，MA20上穿MA60，亏损8%退出，最大仓位10%"})
    assert response.status_code == 201
    assert response.json()["mode"] in {"mock", "deepseek"}
    validated = client.post("/api/ai/strategy/validate", json=response.json()["spec"])
    assert validated.status_code == 200
    assert validated.json()["valid"] is True


def test_invalid_symbol_has_correct_status() -> None:
    response = client.get("/api/market/999999.SH/bars")
    assert response.status_code == 404
