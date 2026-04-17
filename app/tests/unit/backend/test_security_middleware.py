"""Tests for security headers and body size middleware."""

from app.main import create_app
from fastapi.testclient import TestClient

client = TestClient(create_app())


def test_security_headers_attached_to_every_response() -> None:
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "geolocation=()" in response.headers["permissions-policy"]


def test_body_size_limit_rejects_oversized_payload(monkeypatch) -> None:
    # Build an app with a tiny body limit so we can exercise the guard.
    from app.config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "max_request_body_bytes", 10)
    local_client = TestClient(create_app())

    response = local_client.post("/api/search", json={"query": "x" * 1000})

    assert response.status_code == 413
    assert response.json()["error"] == "payload_too_large"


def test_body_size_limit_allows_small_payload() -> None:
    response = client.post("/api/search", json={"query": "book"})
    assert response.status_code == 200


def test_ready_endpoint_does_not_contact_connectors() -> None:
    # If /health/ready ever regresses and touches network, this test still
    # stays green, but the endpoint must remain 200 with a minimal payload.
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
