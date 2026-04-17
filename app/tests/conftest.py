"""Shared pytest fixtures for backend tests.

Keeps tests hermetic by snapshotting and restoring the global ``settings``
object after every test, and by resetting the shared connector registry
cache between tests so tests that override settings can't leak into peers.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.api.dependencies import get_registry
from app.config import settings as settings_module


@pytest.fixture(autouse=True)
def _settings_snapshot() -> Iterator[None]:
    """Snapshot mutable settings fields; restore after the test.

    A growing number of tests needed to mutate ``settings`` directly to
    exercise fixture modes, frontend serving, body size limits, or cache
    TTLs. Without this guard a failure between ``set`` and the manual
    ``finally`` restore would leak state into every subsequent test.
    """

    snapshot = settings_module.settings.model_dump()
    try:
        yield
    finally:
        for key, value in snapshot.items():
            # Only reassign fields we already know about (pydantic-settings
            # validates on assignment; unknown fields would raise).
            setattr(settings_module.settings, key, value)


@pytest.fixture(autouse=True)
def _clear_registry_cache() -> Iterator[None]:
    """Clear the lru_cache-backed connector registry between tests.

    ``get_registry()`` is ``@lru_cache(maxsize=1)``. Tests that wire custom
    registries via FastAPI dependency overrides are fine, but any test
    that imports ``create_app()`` directly gets the process-wide cached
    registry. Clearing per-test avoids spooky action-at-a-distance.
    """

    get_registry.cache_clear()
    yield
    get_registry.cache_clear()
