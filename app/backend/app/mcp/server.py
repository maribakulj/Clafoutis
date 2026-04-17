"""MCP server exposing Clafoutis tools over stdio.

Run from the command line once the ``mcp`` optional extra is installed::

    pip install -e '.[mcp]'
    clafoutis-mcp           # or: python -m app.mcp.server

The server binds to stdio by default (the standard MCP transport for
desktop clients). All tool logic lives in :mod:`app.mcp.tools` and
reuses the exact same services as the REST layer (specs §13: no
business-logic duplication between REST and MCP).
"""

from __future__ import annotations

import json
from typing import Any

from app.api.dependencies import get_registry
from app.connectors.registry import ConnectorRegistry
from app.mcp.tools import MCPTools


def _to_json(value: Any) -> str:
    """Serialize Pydantic models or plain dicts to a compact JSON string."""

    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, ensure_ascii=False, default=str)


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
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> str:
        """Search patrimonial items across registered sources."""

        return _to_json(
            await tools.search_items(
                query=query,
                sources=sources,
                filters=filters,
                page=page,
                page_size=page_size,
            )
        )

    @server.tool()
    async def get_item(global_id: str) -> str:
        """Return a normalized item by its 'source:source_item_id' identifier."""

        return _to_json(await tools.get_item(global_id))

    @server.tool()
    async def resolve_manifest(
        source: str,
        source_item_id: str,
        record_url: str | None = None,
    ) -> str:
        """Resolve a IIIF manifest URL for a known item."""

        return _to_json(
            await tools.resolve_manifest(
                source=source, source_item_id=source_item_id, record_url=record_url
            )
        )

    @server.tool()
    async def open_in_mirador(
        manifest_urls: list[str], workspace: str = "default"
    ) -> str:
        """Return a shareable Mirador workspace state for a list of manifest URLs."""

        return _to_json(
            await tools.open_in_mirador(manifest_urls=manifest_urls, workspace=workspace)
        )

    @server.tool()
    async def list_sources() -> str:
        """List registered sources with capabilities and health flags."""

        return _to_json(await tools.list_sources())

    return server


def run_stdio() -> None:
    """Console script entry point: build the server and run the stdio transport."""

    server = build_server()
    server.run()


if __name__ == "__main__":  # pragma: no cover
    run_stdio()
