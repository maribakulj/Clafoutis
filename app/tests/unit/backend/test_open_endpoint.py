"""Tests for the /api/open Mirador state endpoint."""

from app.main import create_app
from fastapi.testclient import TestClient

client = TestClient(create_app())


def test_open_returns_mirador_state_for_public_manifest() -> None:
    response = client.post(
        "/api/open",
        json={"manifest_urls": ["https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["manifest_urls"] == [
        "https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"
    ]
    assert body["mirador_state"]["windows"][0]["manifestId"] == (
        "https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"
    )
    assert body["mirador_state"]["workspace"]["id"] == "default"


def test_open_dedupes_duplicate_urls() -> None:
    url = "https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"
    response = client.post("/api/open", json={"manifest_urls": [url, url]})
    assert response.status_code == 200
    assert response.json()["manifest_urls"] == [url]


def test_open_rejects_private_ip_manifest_url() -> None:
    response = client.post(
        "/api/open",
        json={"manifest_urls": ["http://127.0.0.1/manifest.json"]},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "bad_request"


def test_open_rejects_empty_url_list() -> None:
    response = client.post("/api/open", json={"manifest_urls": []})
    # Pydantic validation at ingress returns 422 for schema violations.
    assert response.status_code == 422


def test_open_rejects_oversized_url_list() -> None:
    urls = [f"https://example.org/m/{i}/manifest" for i in range(17)]
    response = client.post("/api/open", json={"manifest_urls": urls})
    assert response.status_code == 422
