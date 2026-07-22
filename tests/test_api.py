from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analysis_contract() -> None:
    response = client.get("/api/stocks/600519/analysis?strategy=trend&chart_bars=120")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stock"]["symbol"] == "600519"
    assert len(payload["bars"]) == 120
    assert payload["data_meta"]["source"] in {"demo", "akshare"}


def test_unknown_stock_is_not_accepted() -> None:
    response = client.get("/api/stocks/999999/analysis")
    assert response.status_code == 404

