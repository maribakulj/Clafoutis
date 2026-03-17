"""Frontend static serving behavior tests."""

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.main import create_app


def test_root_serves_frontend_index_when_configured(tmp_path) -> None:
    """Root path should serve SPA index when frontend serving is enabled."""

    original_serve_frontend = settings.serve_frontend
    original_frontend_dist_dir = settings.frontend_dist_dir

    try:
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "index.html").write_text("<html><body>Clafoutis UI</body></html>", encoding="utf-8")

        settings.serve_frontend = True
        settings.frontend_dist_dir = str(dist_dir)

        client = TestClient(create_app())
        response = client.get("/")

        assert response.status_code == 200
        assert "Clafoutis UI" in response.text
    finally:
        settings.serve_frontend = original_serve_frontend
        settings.frontend_dist_dir = original_frontend_dist_dir
