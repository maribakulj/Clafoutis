from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sources() -> None:
    response = client.get("/api/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["sources"]
    source_names = [s["name"] for s in body["sources"]]
    assert "mock" in source_names
    assert "gallica" in source_names
    assert "europeana" in source_names
    assert "bodleian" in source_names


def test_search() -> None:
    response = client.post("/api/search", json={"query": "book", "page": 1, "page_size": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert len(body["sources_used"]) > 0


def test_item() -> None:
    response = client.get("/api/item/mock:ms-1")
    assert response.status_code == 200
    assert response.json()["source_item_id"] == "ms-1"


def test_resolve_manifest() -> None:
    response = client.post(
        "/api/resolve-manifest",
        json={"source": "mock", "source_item_id": "ms-1"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_import() -> None:
    response = client.post("/api/import", json={"url": "https://mock.example.org/items/ms-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["detected_source"] is not None
    assert body["record_url"] == "https://mock.example.org/items/ms-1"


def test_item_rejects_invalid_global_id_format() -> None:
    response = client.get("/api/item/invalid-id")
    assert response.status_code == 400
    assert response.json()["error"] == "bad_request"


def test_import_rejects_non_http_url() -> None:
    response = client.post("/api/import", json={"url": "file:///etc/passwd"})
    assert response.status_code == 400
    assert response.json()["error"] == "bad_request"
