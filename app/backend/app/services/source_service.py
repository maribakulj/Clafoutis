"""Service exposing source capabilities and health state."""

import asyncio

from app.config.settings import settings
from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry
from app.models.source_models import SourceCapabilities, SourceDescriptor, SourcesResponse
from app.utils.ttl_cache import TTLCache


class SourceService:
    """Provide data for ``/api/sources`` endpoint.

    Capabilities and healthcheck results are cached in-memory for the
    duration configured by ``capability_probe_cache_ttl_seconds``. This
    turns ``/api/sources`` and ``/api/health`` from N × remote calls per
    request into at most N calls per TTL window, which is critical for
    public demos where the sources page is often reloaded.
    """

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        ttl = float(settings.capability_probe_cache_ttl_seconds)
        self._capabilities_cache: TTLCache[str, SourceCapabilities] = TTLCache(ttl)
        self._health_cache: TTLCache[str, dict[str, str]] = TTLCache(ttl)

    async def list_sources(self) -> SourcesResponse:
        """Return registered sources with capabilities and health flags."""

        connectors = self._registry.list_connectors()
        results = await asyncio.gather(
            *(self._describe(connector) for connector in connectors)
        )
        return SourcesResponse(sources=list(results))

    async def _describe(self, connector: BaseConnector) -> SourceDescriptor:
        capabilities_task = self._capabilities_cache.get_or_compute(
            connector.name, connector.capabilities
        )
        health_task = self._health_cache.get_or_compute(
            connector.name, connector.healthcheck
        )
        capabilities, health = await asyncio.gather(capabilities_task, health_task)
        return SourceDescriptor(
            name=connector.name,
            label=connector.label,
            source_type=connector.source_type,
            capabilities=capabilities,
            healthy=health.get("status") == "ok",
        )
