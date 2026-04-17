"""Tests for MCP Resources, Prompts and tool annotations.

Only runs when the ``mcp`` optional extra is installed; skips cleanly
otherwise so the default [dev] install test run stays green.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry

pytest.importorskip("mcp.server.fastmcp")


def _registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    return registry


def test_tool_annotations_flag_read_only_and_idempotent() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    tools = asyncio.run(server.list_tools())
    by_name = {tool.name: tool for tool in tools}

    # Read-only tools must advertise readOnlyHint=True, destructiveHint=False.
    for name in ("search_items", "get_item", "resolve_manifest", "list_sources", "import_url"):
        ann = by_name[name].annotations
        assert ann is not None, f"{name} missing annotations"
        assert ann.readOnlyHint is True, f"{name} should be read-only"
        assert ann.destructiveHint is False, f"{name} should not be destructive"

    # open_in_mirador is idempotent but not read-only (returns new state).
    open_ann = by_name["open_in_mirador"].annotations
    assert open_ann is not None
    assert open_ann.idempotentHint is True
    assert open_ann.destructiveHint is False


def test_resources_list_includes_sources() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    resources = asyncio.run(server.list_resources())
    uris = {str(resource.uri) for resource in resources}
    assert "clafoutis://sources" in uris


def test_resource_templates_expose_item_by_id() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    templates = asyncio.run(server.list_resource_templates())
    patterns = {template.uriTemplate for template in templates}
    assert "clafoutis://item/{global_id}" in patterns


def test_resource_read_sources_returns_json_body() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    contents = asyncio.run(server.read_resource("clafoutis://sources"))
    # FastMCP returns a list of ReadResourceContents; first block carries JSON.
    blob = contents[0].content
    payload = json.loads(blob)
    assert {entry["name"] for entry in payload["sources"]} == {"mock"}


def test_resource_read_item_returns_known_mock_record() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    contents = asyncio.run(server.read_resource("clafoutis://item/mock:ms-1"))
    payload = json.loads(contents[0].content)
    assert payload["source"] == "mock"
    assert payload["source_item_id"] == "ms-1"


def test_resource_read_item_missing_bubbles_up_not_found() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    with pytest.raises(Exception, match="not_found|Item"):
        asyncio.run(server.read_resource("clafoutis://item/mock:does-not-exist"))


def test_prompts_include_find_heritage_items() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    prompts = asyncio.run(server.list_prompts())
    names = {prompt.name for prompt in prompts}
    assert "find_heritage_items" in names


def test_get_prompt_renders_parameters() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    result = asyncio.run(
        server.get_prompt(
            "find_heritage_items",
            {"topic": "dante", "iiif_only": "true"},
        )
    )
    # FastMCP normalizes prompts to a list of messages with text content.
    text = result.messages[0].content.text
    assert "dante" in text
    assert "has_iiif_manifest" in text


def test_call_tool_error_mapping_preserves_bad_request_tag() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    # FastMCP wraps tool exceptions in ToolError; the wrapped message must
    # carry the stable ``bad_request:`` prefix so LLM clients can branch.
    with pytest.raises(Exception, match="bad_request"):
        asyncio.run(server.call_tool("get_item", {"global_id": "no-colon"}))


def test_call_tool_error_mapping_preserves_not_found_tag() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    with pytest.raises(Exception, match="not_found"):
        asyncio.run(server.call_tool("get_item", {"global_id": "mock:missing"}))
