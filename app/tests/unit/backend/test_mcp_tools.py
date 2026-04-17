"""Tests for MCP tool wrappers.

These tests exercise the tool functions directly without the MCP SDK so
the test suite stays green without the [mcp] extra installed. The
wrappers must simply delegate to the same services as the REST layer.
"""

import asyncio

import pytest
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.mcp.tools import MCPTools
from app.utils.errors import BadRequestError, NotFoundError


def _tools() -> MCPTools:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    return MCPTools(registry)


def test_search_items_returns_results_like_rest() -> None:
    tools = _tools()
    response = asyncio.run(tools.search_items(query="book"))
    assert response.results
    assert response.sources_used == ["mock"]


def test_search_items_applies_filters() -> None:
    tools = _tools()
    response = asyncio.run(
        tools.search_items(query="book", filters={"has_iiif_manifest": True})
    )
    assert all(item.has_iiif_manifest for item in response.results)


def test_get_item_returns_normalized_item() -> None:
    tools = _tools()
    item = asyncio.run(tools.get_item("mock:ms-1"))
    assert item.source == "mock"
    assert item.source_item_id == "ms-1"


def test_get_item_unknown_raises_not_found() -> None:
    tools = _tools()
    with pytest.raises(NotFoundError):
        asyncio.run(tools.get_item("mock:does-not-exist"))


def test_get_item_invalid_format_raises_bad_request() -> None:
    tools = _tools()
    with pytest.raises(BadRequestError):
        asyncio.run(tools.get_item("no-colon"))


def test_resolve_manifest_returns_known_manifest() -> None:
    tools = _tools()
    response = asyncio.run(tools.resolve_manifest(source="mock", source_item_id="ms-1"))
    assert response.status == "resolved"
    assert response.manifest_url is not None


def test_resolve_manifest_unknown_source_raises() -> None:
    tools = _tools()
    with pytest.raises(NotFoundError):
        asyncio.run(tools.resolve_manifest(source="unknown", source_item_id="x"))


def test_open_in_mirador_returns_workspace_state() -> None:
    tools = _tools()
    response = asyncio.run(
        tools.open_in_mirador(
            manifest_urls=["https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"]
        )
    )
    assert response.manifest_urls == [
        "https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"
    ]
    assert response.mirador_state.workspace["id"] == "default"


def test_open_in_mirador_dedupes() -> None:
    tools = _tools()
    url = "https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"
    response = asyncio.run(tools.open_in_mirador(manifest_urls=[url, url]))
    assert response.manifest_urls == [url]


def test_open_in_mirador_rejects_ssrf_loopback() -> None:
    tools = _tools()
    with pytest.raises(BadRequestError):
        asyncio.run(
            tools.open_in_mirador(manifest_urls=["http://127.0.0.1/manifest.json"])
        )


def test_open_in_mirador_rejects_empty_list() -> None:
    tools = _tools()
    with pytest.raises(BadRequestError):
        asyncio.run(tools.open_in_mirador(manifest_urls=[]))


def test_open_in_mirador_rejects_oversized_list() -> None:
    tools = _tools()
    urls = [f"https://example.org/m/{i}/manifest" for i in range(17)]
    with pytest.raises(BadRequestError):
        asyncio.run(tools.open_in_mirador(manifest_urls=urls))


def test_list_sources_returns_registered_sources() -> None:
    tools = _tools()
    response = asyncio.run(tools.list_sources())
    names = {source.name for source in response.sources}
    assert "mock" in names


def test_mcp_tools_do_not_duplicate_business_logic() -> None:
    """Sanity: MCP tools must use the exact same service classes as REST.

    If a future refactor introduced a parallel MCP-only implementation,
    this test catches the drift by asserting the wrapper holds references
    to the canonical service instances.
    """

    from app.services.item_service import ItemService
    from app.services.manifest_resolver import ManifestResolver
    from app.services.search_orchestrator import SearchOrchestrator
    from app.services.source_service import SourceService

    tools = _tools()
    assert isinstance(tools._search, SearchOrchestrator)
    assert isinstance(tools._items, ItemService)
    assert isinstance(tools._manifests, ManifestResolver)
    assert isinstance(tools._sources, SourceService)
