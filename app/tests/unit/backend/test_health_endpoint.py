"""Tests for the enriched health endpoint."""

from app.main import create_app
from fastapi.testclient import TestClient

client = TestClient(create_app())


def test_health_returns_connector_statuses() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert "connectors" in body
    assert "duration_ms" in body
    assert body["status"] in ("ok", "degraded")
    assert isinstance(body["connectors"], dict)
    assert len(body["connectors"]) > 0


def test_health_includes_all_registered_connectors() -> None:
    response = client.get("/api/health")
    body = response.json()
    connector_names = set(body["connectors"].keys())
    assert "mock" in connector_names
    assert "gallica" in connector_names
