"""Async HTTP client utilities for connector network calls."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from app.config.settings import settings

_shared_client: httpx.AsyncClient | None = None


def _get_or_create_client() -> httpx.AsyncClient:
    """Return a shared AsyncClient, creating one if needed."""
    global _shared_client  # noqa: PLW0603
    if _shared_client is None or _shared_client.is_closed:
        timeout = httpx.Timeout(settings.request_timeout_seconds)
        _shared_client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    return _shared_client


@asynccontextmanager
async def build_async_client() -> AsyncIterator[httpx.AsyncClient]:
    """Yield a shared AsyncClient. The connection pool is kept alive."""
    yield _get_or_create_client()
