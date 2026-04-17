"""MCP tool implementations.

These are thin service wrappers that reuse the exact same backend services
as the REST layer (per specs §13: no business-logic duplication). They
return plain Python / Pydantic objects and have no dependency on the MCP
SDK, so they are testable in isolation and reusable from any transport.
"""

from __future__ import annotations

from typing import Any

from app.connectors.registry import ConnectorRegistry
from app.models.import_models import ImportResponse
from app.models.manifest_models import (
    OpenInMiradorResponse,
    ResolveManifestRequest,
    ResolveManifestResponse,
)
from app.models.normalized_item import NormalizedItem
from app.models.search_models import (
    SearchFilters,
    SearchRequest,
    SearchResponse,
)
from app.models.source_models import SourcesResponse
from app.services.import_service import ImportService
from app.services.item_service import ItemService
from app.services.manifest_resolver import ManifestResolver
from app.services.search_orchestrator import SearchOrchestrator
from app.services.source_service import SourceService
from app.utils.errors import BadRequestError
from app.utils.url_validation import validate_http_url


class MCPTools:
    """Grouping of MCP-exposed operations.

    Instantiated with a ``ConnectorRegistry`` so tests and the server can
    inject either a production registry or a stub. Each method mirrors the
    corresponding REST endpoint and returns a Pydantic model (models know
    how to serialize to JSON-safe dicts).
    """

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._search = SearchOrchestrator(registry)
        self._items = ItemService(registry)
        self._manifests = ManifestResolver(registry)
        self._sources = SourceService(registry)
        self._import = ImportService(registry)

    async def search_items(
        self,
        query: str,
        sources: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> SearchResponse:
        """Run federated search across selected connectors."""

        search_filters = SearchFilters(**(filters or {}))
        request = SearchRequest(
            query=query,
            sources=sources,
            filters=search_filters,
            page=page,
            page_size=page_size,
        )
        return await self._search.search(request)

    async def get_item(self, global_id: str) -> NormalizedItem:
        """Return a normalized item by its ``source:source_item_id`` identifier."""

        return await self._items.get_item(global_id)

    async def resolve_manifest(
        self,
        source: str,
        source_item_id: str,
        record_url: str | None = None,
    ) -> ResolveManifestResponse:
        """Resolve a IIIF manifest URL for a known item."""

        request = ResolveManifestRequest(
            source=source, source_item_id=source_item_id, record_url=record_url
        )
        return await self._manifests.resolve(request)

    async def open_in_mirador(
        self,
        manifest_urls: list[str],
        workspace: str = "default",
    ) -> OpenInMiradorResponse:
        """Validate manifest URLs and return a shareable Mirador workspace state."""

        if not manifest_urls:
            raise BadRequestError("manifest_urls must not be empty")
        if len(manifest_urls) > 16:
            raise BadRequestError("manifest_urls must contain at most 16 entries")

        deduped: list[str] = []
        seen: set[str] = set()
        for raw in manifest_urls:
            safe = validate_http_url(raw)
            if safe in seen:
                continue
            seen.add(safe)
            deduped.append(safe)

        from app.models.manifest_models import MiradorWorkspaceState

        windows = [{"manifestId": url} for url in deduped]
        state = MiradorWorkspaceState(
            windows=windows,
            catalog=windows,
            workspace={
                "id": workspace,
                "viewingDirection": "left-to-right",
                "showZoomControls": True,
            },
        )
        return OpenInMiradorResponse(manifest_urls=deduped, mirador_state=state)

    async def list_sources(self) -> SourcesResponse:
        """List registered sources with capabilities and health flags."""

        return await self._sources.list_sources()

    async def import_url(self, url: str) -> ImportResponse:
        """Validate a free-form URL and attempt manifest resolution."""

        return await self._import.import_url(url)
