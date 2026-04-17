"""Tests for caching in SourceService."""

import asyncio

from app.config import settings as settings_module
from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry
from app.models.source_models import SourceCapabilities
from app.services.source_service import SourceService


class _CountingConnector(BaseConnector):
    name = "counting"
    label = "Counting"
    source_type = "stub"

    def __init__(self) -> None:
        self.capabilities_calls = 0
        self.health_calls = 0

    async def search(self, query, filters, page, page_size):
        raise NotImplementedError

    async def get_item(self, source_item_id):
        return None

    async def resolve_manifest(self, item=None, record_url=None):
        return None

    async def healthcheck(self):
        self.health_calls += 1
        return {"status": "ok"}

    async def capabilities(self):
        self.capabilities_calls += 1
        return SourceCapabilities()


def test_source_service_caches_healthcheck_and_capabilities(monkeypatch) -> None:
    monkeypatch.setattr(settings_module.settings, "capability_probe_cache_ttl_seconds", 60)

    connector = _CountingConnector()
    registry = ConnectorRegistry()
    registry.register(connector)
    service = SourceService(registry)

    async def run() -> None:
        await service.list_sources()
        await service.list_sources()
        await service.list_sources()

    asyncio.run(run())

    # Three calls to list_sources but only one call per remote operation.
    assert connector.capabilities_calls == 1
    assert connector.health_calls == 1


def test_source_service_runs_sources_in_parallel() -> None:
    """Slow source must not serially delay the response.

    Two connectors each sleep 0.1s; running them serially would take >=0.2s,
    in parallel it should complete well under that.
    """

    import time

    class _SlowConnector(_CountingConnector):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.name = name
            self.label = name

        async def healthcheck(self):
            await asyncio.sleep(0.1)
            return {"status": "ok"}

        async def capabilities(self):
            await asyncio.sleep(0.1)
            return SourceCapabilities()

    registry = ConnectorRegistry()
    registry.register(_SlowConnector("a"))
    registry.register(_SlowConnector("b"))
    service = SourceService(registry)

    start = time.perf_counter()
    asyncio.run(service.list_sources())
    elapsed = time.perf_counter() - start

    # Serial would be ~0.2s; parallel should be ~0.1s. Leave comfortable slack.
    assert elapsed < 0.18
