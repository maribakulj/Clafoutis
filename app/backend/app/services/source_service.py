"""Service exposing source capabilities and health state."""

from app.connectors.registry import ConnectorRegistry
from app.models.source_models import SourceDescriptor, SourcesResponse


class SourceService:
    """Provide data for `/api/sources` endpoint."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def list_sources(self) -> SourcesResponse:
        """Return registered sources with capabilities and health flags."""

        sources: list[SourceDescriptor] = []
        for connector in self._registry.list_connectors():
            capabilities = await connector.capabilities()
            health = await connector.healthcheck()
            sources.append(
                SourceDescriptor(
                    name=connector.name,
                    label=connector.label,
                    source_type=connector.source_type,
                    capabilities=capabilities,
                    healthy=health.get("status") == "ok",
                )
            )
        return SourcesResponse(sources=sources)
