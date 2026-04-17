"""Tests for the second wave of MCP server improvements.

Covers:
- server instructions field
- additional prompts (compare_items, explore_source)
- schema resource (clafoutis://schema/normalized_item)
- Context injection on search_items (progress + info notifications)
- lifespan hook calling reset_shared_client on shutdown

Skipped when the ``mcp`` optional extra is not installed.
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


def test_server_exposes_instructions() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    assert server.instructions is not None
    assert "Clafoutis" in server.instructions
    assert "search_items" in server.instructions


def test_all_three_prompts_are_registered() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    prompts = asyncio.run(server.list_prompts())
    names = {p.name for p in prompts}
    assert names == {"find_heritage_items", "compare_items", "explore_source"}


def test_compare_items_prompt_interpolates_both_ids() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    result = asyncio.run(
        server.get_prompt(
            "compare_items",
            {"global_id_a": "mock:ms-1", "global_id_b": "gallica:ark-123"},
        )
    )
    text = result.messages[0].content.text
    assert "mock:ms-1" in text
    assert "gallica:ark-123" in text
    assert "open_in_mirador" in text


def test_explore_source_prompt_interpolates_source() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    result = asyncio.run(
        server.get_prompt(
            "explore_source", {"source": "gallica", "sample_query": "dante"}
        )
    )
    text = result.messages[0].content.text
    assert "gallica" in text
    assert "dante" in text


def test_schema_resource_returns_json_schema_for_normalized_item() -> None:
    from app.mcp.server import build_server

    server = build_server(registry=_registry())
    contents = asyncio.run(
        server.read_resource("clafoutis://schema/normalized_item")
    )
    payload = json.loads(contents[0].content)
    assert payload.get("title") == "NormalizedItem"
    # A handful of expected properties should appear in the schema.
    properties = payload.get("properties", {})
    for field in ("id", "source", "source_item_id", "title", "manifest_url"):
        assert field in properties


def test_search_items_emits_progress_and_info_via_context() -> None:
    """Call search_items through FastMCP and capture the Context messages.

    We don't need a full client; FastMCP's internal Context routes log and
    progress calls through a handler we can stub.
    """

    from app.config.settings import settings
    from app.mcp.server import build_server

    settings.gallica_use_fixtures = True
    settings.bodleian_use_fixtures = True
    settings.europeana_use_fixtures = True

    server = build_server(registry=_registry())

    progress_events: list[tuple[float, float | None, str | None]] = []
    infos: list[str] = []

    async def fake_report_progress(self, progress, total=None, message=None):
        progress_events.append((progress, total, message))

    async def fake_info(self, message, **kwargs):
        infos.append(message)

    from mcp.server.fastmcp import Context

    Context.report_progress = fake_report_progress  # type: ignore[method-assign]
    Context.info = fake_info  # type: ignore[method-assign]

    async def run() -> None:
        _, _ = await server.call_tool("search_items", {"query": "book"})

    asyncio.run(run())

    assert progress_events, "search_items should emit progress events"
    # We issue a starting 0/2 and a completing 2/2 notification.
    assert progress_events[0][0] == 0
    assert progress_events[-1][0] == 2
    assert infos, "search_items should log an info message"
    assert any("Federating search" in msg for msg in infos)


def test_lifespan_closes_shared_httpx_client_on_shutdown(monkeypatch) -> None:
    """The lifespan contextmanager must call reset_shared_client() on teardown."""

    from app.mcp import server as server_module

    called: list[bool] = []

    async def fake_reset() -> None:
        called.append(True)

    monkeypatch.setattr(server_module, "reset_shared_client", fake_reset)

    async def run() -> None:
        async with server_module._lifespan(None):
            pass

    asyncio.run(run())
    assert called == [True]
