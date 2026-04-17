"""Tests for the async TTL cache used by source capability/health caching."""

import asyncio

from app.utils.ttl_cache import TTLCache


def test_ttl_cache_returns_cached_value_within_ttl() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    calls = 0

    async def compute() -> int:
        nonlocal calls
        calls += 1
        return 42

    async def run() -> tuple[int, int]:
        a = await cache.get_or_compute("k", compute)
        b = await cache.get_or_compute("k", compute)
        return a, b

    a, b = asyncio.run(run())
    assert a == 42 and b == 42
    assert calls == 1


def test_ttl_cache_recomputes_after_expiry() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=0)  # expire immediately
    calls = 0

    async def compute() -> int:
        nonlocal calls
        calls += 1
        return calls

    async def run() -> list[int]:
        return [
            await cache.get_or_compute("k", compute),
            await cache.get_or_compute("k", compute),
        ]

    # With ttl=0 and monotonic time advancing, the second call must re-enter.
    results = asyncio.run(run())
    assert calls == 2
    assert results == [1, 2]


def test_ttl_cache_coalesces_concurrent_misses() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    calls = 0
    started = asyncio.Event()

    async def compute() -> int:
        nonlocal calls
        calls += 1
        started.set()
        await asyncio.sleep(0.01)
        return 7

    async def run() -> list[int]:
        tasks = [
            asyncio.create_task(cache.get_or_compute("k", compute)) for _ in range(5)
        ]
        return await asyncio.gather(*tasks)

    results = asyncio.run(run())
    assert results == [7] * 5
    # Single underlying call even though 5 tasks requested the key.
    assert calls == 1


def test_ttl_cache_invalidate_forces_recompute() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    calls = 0

    async def compute() -> int:
        nonlocal calls
        calls += 1
        return calls

    async def run() -> list[int]:
        first = await cache.get_or_compute("k", compute)
        cache.invalidate("k")
        second = await cache.get_or_compute("k", compute)
        return [first, second]

    results = asyncio.run(run())
    assert calls == 2
    assert results == [1, 2]
