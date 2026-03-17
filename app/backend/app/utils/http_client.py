"""Async HTTP client utilities for connector network calls."""

import httpx

from app.config.settings import settings


async def build_async_client() -> httpx.AsyncClient:
    """Create an AsyncClient configured with MVP-safe defaults."""

    timeout = httpx.Timeout(settings.request_timeout_seconds)
    return httpx.AsyncClient(timeout=timeout, follow_redirects=True)
