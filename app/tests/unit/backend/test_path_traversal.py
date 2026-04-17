"""Test that SPA catch-all rejects path traversal attempts."""

from app.config.settings import settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_spa_rejects_path_traversal(monkeypatch, tmp_path) -> None:
    """Verify that ../../etc/passwd does not leak files outside frontend_dist."""

    index = tmp_path / "index.html"
    index.write_text("<html></html>")

    monkeypatch.setattr(settings, "serve_frontend", True)
    monkeypatch.setattr(settings, "frontend_dist_dir", str(tmp_path))

    client = TestClient(create_app())
    response = client.get("/../../etc/passwd")
    # Should either return 400 (invalid path) or fall through to index.
    assert response.status_code in (400, 200)
    if response.status_code == 200:
        # Must return index.html, not /etc/passwd.
        assert "<html>" in response.text
