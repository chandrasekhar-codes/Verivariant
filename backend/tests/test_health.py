from fastapi.testclient import TestClient

from app.config import DISCLAIMER
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["disclaimer"] == DISCLAIMER


def test_root_includes_disclaimer() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["disclaimer"] == DISCLAIMER
