"""Integration tests for the MCP server wiring.

These tests only run when the ``mcp`` optional extra is installed; on a
bare [dev] install they skip cleanly so the rest of the test suite stays
green. They guarantee that:

- the server actually boots with FastMCP,
- every tool is registered and discoverable via ``list_tools``,
- tool input schemas expose the typed filter shape (not ``{type: object,
  additionalProperties: true}``),
- calling a tool yields structured JSON content that matches the
  underlying service response — i.e. MCP clients get Pydantic-level
  fidelity without having to re-parse stringified JSON.
"""

from __future__ import annotations

import asyncio

import pytest
from app.config.settings import settings
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry

mcp_sdk = pytest.importorskip("mcp.server.fastmcp")


def _isolated_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    return registry


def test_build_server_registers_every_expected_tool() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_isolated_registry())
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert {
        "search_items",
        "get_item",
        "resolve_manifest",
        "open_in_mirador",
        "list_sources",
        "import_url",
    }.issubset(names)


def test_search_items_schema_exposes_typed_filters() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_isolated_registry())
    tools = asyncio.run(server.list_tools())
    search = next(t for t in tools if t.name == "search_items")

    schema = search.inputSchema
    filters_ref = schema["properties"]["filters"]
    # anyOf variant pointing to the SearchFilters schema, never a bare
    # "{type: object, additionalProperties: true}" blob.
    assert "$ref" in str(filters_ref) or "SearchFilters" in str(schema.get("$defs", {}))
    assert "SearchFilters" in schema.get("$defs", {})
    filter_props = schema["$defs"]["SearchFilters"]["properties"]
    assert "has_iiif_manifest" in filter_props
    assert "object_type" in filter_props
    assert "languages" in filter_props


def test_call_list_sources_returns_structured_content() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_isolated_registry())
    _, structured = asyncio.run(server.call_tool("list_sources", {}))
    assert isinstance(structured, dict)
    assert "sources" in structured
    # One source (mock) registered in the isolated registry.
    names = {entry["name"] for entry in structured["sources"]}
    assert names == {"mock"}


def test_call_search_items_with_filter_returns_structured_payload(monkeypatch) -> None:
    from app.mcp.server import build_server

    monkeypatch.setattr(settings, "gallica_use_fixtures", True)
    monkeypatch.setattr(settings, "bodleian_use_fixtures", True)
    monkeypatch.setattr(settings, "europeana_use_fixtures", True)

    server = build_server(registry=_isolated_registry())
    _, structured = asyncio.run(
        server.call_tool(
            "search_items",
            {"query": "book", "filters": {"has_iiif_manifest": True}},
        )
    )

    assert isinstance(structured, dict)
    assert structured["query"] == "book"
    assert "results" in structured
    assert all(item["has_iiif_manifest"] for item in structured["results"])


def test_call_open_in_mirador_validates_ssrf() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_isolated_registry())
    with pytest.raises(Exception, match="URL host is not allowed|bad_request"):
        asyncio.run(
            server.call_tool(
                "open_in_mirador",
                {"manifest_urls": ["http://127.0.0.1/manifest.json"]},
            )
        )
