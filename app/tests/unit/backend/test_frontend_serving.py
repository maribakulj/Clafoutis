"""Frontend static serving behavior tests."""

from app.config.settings import settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_root_serves_frontend_index_when_configured(monkeypatch, tmp_path) -> None:
    """Root path should serve SPA index when frontend serving is enabled."""

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html><body>Clafoutis UI</body></html>", encoding="utf-8")

    monkeypatch.setattr(settings, "serve_frontend", True)
    monkeypatch.setattr(settings, "frontend_dist_dir", str(dist_dir))

    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "Clafoutis UI" in response.text
