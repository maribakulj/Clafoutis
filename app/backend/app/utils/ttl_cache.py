"""Small async-safe in-memory TTL cache for connector healthchecks and capabilities."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """Minimal asyncio-safe TTL cache.

    Coalesces concurrent misses for the same key using a per-key lock so a
    single upstream call serves multiple waiters. Not thread-safe; designed
    for the single-event-loop FastAPI app.
    """

    def __init__(self, ttl_seconds: float) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0")
        self._ttl = ttl_seconds
        self._entries: dict[K, tuple[float, V]] = {}
        self._locks: dict[K, asyncio.Lock] = {}

    async def get_or_compute(
        self, key: K, compute: Callable[[], Awaitable[V]]
    ) -> V:
        """Return the cached value for ``key`` or call ``compute`` and cache it."""

        now = time.monotonic()
        entry = self._entries.get(key)
        if entry is not None and (now - entry[0]) <= self._ttl:
            return entry[1]

        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            # Another waiter may have populated it while we were queued.
            entry = self._entries.get(key)
            now = time.monotonic()
            if entry is not None and (now - entry[0]) <= self._ttl:
                return entry[1]
            value = await compute()
            self._entries[key] = (time.monotonic(), value)
            return value

    def invalidate(self, key: K) -> None:
        self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()
