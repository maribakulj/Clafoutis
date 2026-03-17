"""Startup import smoke tests for deployment robustness."""

from __future__ import annotations

import os
import subprocess
import sys


def test_importing_main_with_descriptive_env_values_does_not_crash() -> None:
    """Importing app.main should not fail even with descriptive HF Space env values."""

    env = os.environ.copy()
    env["CLAFOUTIS_SERVE_FRONTEND"] = "Serve the built frontend from the backend"
    env["CLAFOUTIS_BODLEIAN_USE_FIXTURES"] = "Use fixture data for Bodleian connector to keep the demo stable"

    completed = subprocess.run(
        [sys.executable, "-c", "from app.main import app; print(app.title)"],
        cwd="app/backend",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Clafoutis Backend" in completed.stdout
