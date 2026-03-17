"""Service exposing source capabilities and health state."""

from app.connectors.registry import ConnectorRegistry
from app.models.source_models import SourceDescriptor, SourcesResponse
from app.utils.probing.prober import CapabilityProber


class SourceService:
    """Provide data for `/api/sources` endpoint."""

    def __init__(self, registry: ConnectorRegistry, prober: CapabilityProber) -> None:
        self._registry = registry
        self._prober = prober

    async def list_sources(self) -> SourcesResponse:
        """Return registered sources with declared/detected/effective capabilities."""

        sources: list[SourceDescriptor] = []
        for connector in self._registry.list_connectors():
            capabilities = await connector.capabilities()
            declared = capabilities.to_runtime_capabilities()
            probe_snapshot = await self._prober.probe(connector, declared)
            health = await connector.healthcheck()
            sources.append(
                SourceDescriptor(
                    name=connector.name,
                    label=connector.label,
                    source_type=connector.source_type,
                    capabilities=capabilities,
                    healthy=health.get("status") == "ok",
                    declared_capabilities=declared,
                    detected_capabilities=probe_snapshot.detected_capabilities,
                    effective_capabilities=probe_snapshot.effective_capabilities,
                    probe_status=probe_snapshot.probe_status,
                    probe_message=probe_snapshot.probe_message,
                    probe_timestamp=probe_snapshot.probe_timestamp,
                    probe_source=probe_snapshot.probe_source,
                    supports_runtime_detection=probe_snapshot.supports_runtime_detection,
                    capability_warnings=probe_snapshot.capability_warnings,
                )
            )
        return SourcesResponse(sources=sources)
