"""MCP server exposing Clafoutis tools, resources and prompts.

Supported transports
--------------------

The server can run over three MCP transports:

- ``stdio``   — standard desktop-client transport (Claude Desktop, etc.)
- ``sse``     — Server-Sent Events over HTTP (browser / HTTP clients)
- ``streamable-http`` — bidirectional HTTP streaming, the recommended
  transport for web-hosted deployments such as Hugging Face Spaces

Console scripts::

    clafoutis-mcp              # stdio (default)
    clafoutis-mcp-http         # streamable HTTP (0.0.0.0:8765 by default)

All three transports are served by the same :class:`FastMCP` instance
built by :func:`build_server`, which delegates to
:class:`app.mcp.tools.MCPTools`. No business logic lives in this module
— it only wires MCP concepts (tools / resources / prompts) to the same
services as the REST layer (specs §13).
"""

from __future__ import annotations

import logging
import os
from typing import Any, cast

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
from app.utils.error_sanitizer import sanitize_error_message
from app.utils.errors import AppError, BadRequestError, NotFoundError

logger = logging.getLogger(__name__)


def _mcp_error_from(exc: Exception) -> Exception:
    """Convert a domain exception into an MCP-friendly error.

    FastMCP serializes the string representation of raised exceptions to the
    client. Sanitize the message to prevent secret leakage and prepend a
    stable error tag so LLM clients can branch on it.
    """

    if isinstance(exc, BadRequestError):
        tag = "bad_request"
    elif isinstance(exc, NotFoundError):
        tag = "not_found"
    elif isinstance(exc, AppError):
        tag = "application_error"
    else:
        return exc
    return type(exc)(f"{tag}: {sanitize_error_message(exc)}")


def _register_tools(server: Any, tools: MCPTools) -> None:  # noqa: C901 - tool wiring is linear but many in one place
    """Register every MCP tool on the FastMCP server."""

    from mcp.types import ToolAnnotations

    read_only = ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, openWorldHint=True
    )
    idempotent = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    @server.tool(annotations=read_only)
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

        try:
            return await tools.search_items(
                query=query,
                sources=sources,
                filters=filters.model_dump(exclude_none=True) if filters else None,
                page=page,
                page_size=page_size,
            )
        except AppError as exc:
            raise _mcp_error_from(exc) from exc

    @server.tool(annotations=read_only)
    async def get_item(global_id: str) -> NormalizedItem:
        """Return a normalized item by its 'source:source_item_id' identifier."""

        try:
            return await tools.get_item(global_id)
        except AppError as exc:
            raise _mcp_error_from(exc) from exc

    @server.tool(annotations=read_only)
    async def resolve_manifest(
        source: str,
        source_item_id: str,
        record_url: str | None = None,
    ) -> ResolveManifestResponse:
        """Resolve a IIIF manifest URL for a known item."""

        try:
            return await tools.resolve_manifest(
                source=source, source_item_id=source_item_id, record_url=record_url
            )
        except AppError as exc:
            raise _mcp_error_from(exc) from exc

    @server.tool(annotations=idempotent)
    async def open_in_mirador(
        manifest_urls: list[str], workspace: str = "default"
    ) -> OpenInMiradorResponse:
        """Return a shareable Mirador workspace state for a list of manifest URLs.

        Every URL is validated against SSRF rules (HTTPS/HTTP only, no private
        or loopback hosts, no credentials). Duplicate URLs collapse to one.
        """

        try:
            return await tools.open_in_mirador(
                manifest_urls=manifest_urls, workspace=workspace
            )
        except AppError as exc:
            raise _mcp_error_from(exc) from exc

    @server.tool(annotations=read_only)
    async def list_sources() -> SourcesResponse:
        """List registered sources with capabilities and health flags."""

        return await tools.list_sources()

    @server.tool(annotations=read_only)
    async def import_url(url: str) -> ImportResponse:
        """Validate a free-form URL and attempt manifest resolution."""

        try:
            return await tools.import_url(url)
        except AppError as exc:
            raise _mcp_error_from(exc) from exc


def _register_resources(server: Any, tools: MCPTools) -> None:
    """Register MCP Resources and Resource Templates on the FastMCP server."""

    @server.resource(
        "clafoutis://sources",
        name="sources",
        title="Registered cultural-heritage sources",
        description=(
            "Read-only snapshot of every registered source with its capabilities "
            "and health status. Useful for clients to discover what to filter on."
        ),
        mime_type="application/json",
    )
    async def sources_resource() -> dict[str, Any]:
        response = await tools.list_sources()
        return cast(dict[str, Any], response.model_dump())

    @server.resource(
        "clafoutis://item/{global_id}",
        name="item",
        title="Normalized item by global id",
        description=(
            "Fetch a single NormalizedItem by its ``source:source_item_id`` "
            "identifier. Same payload as the REST /api/item/{id} endpoint."
        ),
        mime_type="application/json",
    )
    async def item_resource(global_id: str) -> dict[str, Any]:
        try:
            item = await tools.get_item(global_id)
        except AppError as exc:
            raise _mcp_error_from(exc) from exc
        return cast(dict[str, Any], item.model_dump())


def _register_prompts(server: Any) -> None:
    """Register reusable MCP prompts on the FastMCP server."""

    @server.prompt(
        name="find_heritage_items",
        title="Find heritage items across federated sources",
        description=(
            "Starter prompt that asks the model to search Clafoutis for a topic "
            "and summarize the results. Parameterized so clients can reuse it."
        ),
    )
    def find_heritage_items(
        topic: str,
        sources: str | None = None,
        iiif_only: bool = False,
    ) -> str:
        """Prompt template: search for heritage items about ``topic``."""

        filter_hint = " Use filters={has_iiif_manifest: true}." if iiif_only else ""
        sources_hint = (
            f" Restrict to sources={sources.split(',')}." if sources else ""
        )
        return (
            f"You are helping a researcher explore cultural-heritage collections.\n"
            f"Call the `search_items` tool with query=\"{topic}\"."
            f"{sources_hint}{filter_hint}\n"
            "Then summarize the 5 most relevant results: for each, give title, "
            "institution, date, and whether a IIIF manifest is available. "
            "Suggest follow-up searches if results are sparse."
        )


def build_server(registry: ConnectorRegistry | None = None):
    """Build a FastMCP server wired to Clafoutis tools, resources and prompts.

    ``mcp`` is imported lazily so the default backend install stays slim
    and REST tests run without the optional extra.
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
    _register_tools(server, tools)
    _register_resources(server, tools)
    _register_prompts(server)
    return server


# --- Transports / console entry points ---------------------------------------


def run_stdio() -> None:
    """Console script entry point: run the server over stdio."""

    build_server().run("stdio")


def run_http() -> None:
    """Console script entry point: run the server over streamable HTTP.

    Reads ``CLAFOUTIS_MCP_HOST`` and ``CLAFOUTIS_MCP_PORT`` to bind.
    Defaults to ``0.0.0.0:8765`` so the server is reachable from a
    container orchestrator. Suitable for hosted deployments.
    """

    host = os.environ.get("CLAFOUTIS_MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("CLAFOUTIS_MCP_PORT", "8765"))
    server = build_server()
    # FastMCP exposes server.settings for host/port; set before run().
    server.settings.host = host
    server.settings.port = port
    server.run("streamable-http")


if __name__ == "__main__":  # pragma: no cover
    run_stdio()
