"""MCP server exposing Clafoutis tools over stdio.

Run from the command line once the ``mcp`` optional extra is installed::

    pip install -e '.[mcp]'
    clafoutis-mcp           # or: python -m app.mcp.server

The server binds to stdio by default (the standard MCP transport for
desktop clients). All tool logic lives in :mod:`app.mcp.tools` and
reuses the exact same services as the REST layer (specs §13: no
business-logic duplication between REST and MCP).

Tools accept typed Pydantic parameters and return typed Pydantic
responses, so FastMCP generates accurate JSON Schemas for both sides
and emits structured content that MCP clients can consume without
re-parsing stringified JSON.
"""

from __future__ import annotations

from app.api.dependencies import get_registry
from app.connectors.registry import ConnectorRegistry
from app.mcp.tools import MCPTools
from app.models.import_models import ImportResponse
from app.models.manifest_models import (
    OpenInMiradorResponse,
    ResolveManifestResponse,
)
from app.models.normalized_item import NormalizedItem
from app.models.search_models import (
    SearchFilters,
    SearchResponse,
)
from app.models.source_models import SourcesResponse


def build_server(registry: ConnectorRegistry | None = None):
    """Build a FastMCP server wired to Clafoutis tools.

    The ``mcp`` package is an optional dependency; importing it lazily keeps
    the default backend install lightweight and lets the REST tests run
    without the SDK.
    """

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as err:  # pragma: no cover - import guarded at runtime
        raise RuntimeError(
            "The 'mcp' extra is required to run the MCP server. "
            "Install with: pip install -e '.[mcp]'"
        ) from err

    tools = MCPTools(registry or get_registry())
    server = FastMCP("clafoutis")

    @server.tool()
    async def search_items(
        query: str,
        sources: list[str] | None = None,
        filters: SearchFilters | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> SearchResponse:
        """Search patrimonial items across registered sources.

        Returns a normalized SearchResponse with paginated results, a
        ``has_next_page`` flag and partial-failure diagnostics per source.
        """

        return await tools.search_items(
            query=query,
            sources=sources,
            filters=filters.model_dump(exclude_none=True) if filters else None,
            page=page,
            page_size=page_size,
        )

    @server.tool()
    async def get_item(global_id: str) -> NormalizedItem:
        """Return a normalized item by its 'source:source_item_id' identifier."""

        return await tools.get_item(global_id)

    @server.tool()
    async def resolve_manifest(
        source: str,
        source_item_id: str,
        record_url: str | None = None,
    ) -> ResolveManifestResponse:
        """Resolve a IIIF manifest URL for a known item."""

        return await tools.resolve_manifest(
            source=source, source_item_id=source_item_id, record_url=record_url
        )

    @server.tool()
    async def open_in_mirador(
        manifest_urls: list[str], workspace: str = "default"
    ) -> OpenInMiradorResponse:
        """Return a shareable Mirador workspace state for a list of manifest URLs.

        Every URL is validated against SSRF rules (HTTPS/HTTP only, no private
        or loopback hosts, no credentials). Duplicate URLs collapse to one.
        """

        return await tools.open_in_mirador(
            manifest_urls=manifest_urls, workspace=workspace
        )

    @server.tool()
    async def list_sources() -> SourcesResponse:
        """List registered sources with capabilities and health flags."""

        return await tools.list_sources()

    @server.tool()
    async def import_url(url: str) -> ImportResponse:
        """Validate a free-form URL and attempt manifest resolution."""

        return await tools.import_url(url)

    return server


def run_stdio() -> None:
    """Console script entry point: build the server and run the stdio transport."""

    server = build_server()
    server.run()


if __name__ == "__main__":  # pragma: no cover
    run_stdio()
