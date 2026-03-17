"""Basic smoke check for API health endpoint."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "app" / "backend"))

from app.main import create_app


if __name__ == "__main__":
    client = TestClient(create_app())
    response = client.get("/api/health")
    if response.status_code != 200:
        raise SystemExit(f"health failed: {response.status_code} {response.text}")
    print("smoke_ok")
