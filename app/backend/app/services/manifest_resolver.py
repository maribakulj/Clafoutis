"""Service responsible for manifest resolution through connectors."""

from app.connectors.registry import ConnectorRegistry
from app.models.manifest_models import ResolveManifestRequest, ResolveManifestResponse
from app.utils.errors import NotFoundError
from app.utils.ids import make_global_id


class ManifestResolver:
    """Resolve manifests by delegating to source connectors."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def resolve(self, request: ResolveManifestRequest) -> ResolveManifestResponse:
        """Resolve manifest URL for a source item identifier."""

        if not self._registry.has(request.source):
            raise NotFoundError(f"Unknown source '{request.source}'")
        connector = self._registry.get(request.source)
        item = await connector.get_item(request.source_item_id)
        manifest_url = await connector.resolve_manifest(item=item, record_url=request.record_url)
        status = "resolved" if manifest_url else "not_found"
        method = "metadata" if manifest_url else None
        return ResolveManifestResponse(manifest_url=manifest_url, status=status, method=method)

    async def openable_global_id(self, source: str, source_item_id: str) -> str:
        """Return deterministic global id associated to manifest operation."""

        return make_global_id(source, source_item_id)
