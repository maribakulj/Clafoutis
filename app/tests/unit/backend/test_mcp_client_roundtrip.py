"""End-to-end test: MCP client connects to MCP server over stdio.

Spawns the real ``python -m app.mcp.server`` subprocess, initializes a
``ClientSession`` from the official SDK, and exercises each MCP surface.
This guards against breakage in the glue between FastMCP, our server
module and the stdio transport — things unit tests of ``build_server``
alone cannot catch.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import pytest

pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


async def _with_session(callback):
    env = os.environ.copy()
    env["CLAFOUTIS_GALLICA_USE_FIXTURES"] = "true"
    env["CLAFOUTIS_BODLEIAN_USE_FIXTURES"] = "true"
    env["CLAFOUTIS_EUROPEANA_USE_FIXTURES"] = "true"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        env=env,
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        return await callback(session)


def test_client_roundtrip_lists_every_surface() -> None:
    async def check(session: ClientSession) -> None:
        tools = await session.list_tools()
        assert {t.name for t in tools.tools} >= {
            "search_items", "get_item", "resolve_manifest",
            "open_in_mirador", "list_sources", "import_url",
        }

        resources = await session.list_resources()
        assert any(str(r.uri) == "clafoutis://sources" for r in resources.resources)

        templates = await session.list_resource_templates()
        assert any(
            t.uriTemplate == "clafoutis://item/{global_id}"
            for t in templates.resourceTemplates
        )

        prompts = await session.list_prompts()
        assert {p.name for p in prompts.prompts} >= {"find_heritage_items"}

    asyncio.run(_with_session(check))


def test_client_reads_sources_resource() -> None:
    async def check(session: ClientSession) -> None:
        result = await session.read_resource("clafoutis://sources")
        text_blocks = [getattr(c, "text", "") for c in result.contents]
        payload = json.loads(text_blocks[0])
        names = {entry["name"] for entry in payload["sources"]}
        assert {"mock", "gallica", "bodleian", "europeana"} <= names

    asyncio.run(_with_session(check))


def test_client_calls_search_items_and_gets_structured_content() -> None:
    async def check(session: ClientSession) -> None:
        result = await session.call_tool(
            "search_items", {"query": "book", "page_size": 5}
        )
        # Structured content available on FastMCP-emitted CallToolResult.
        assert result.structuredContent is not None
        assert "results" in result.structuredContent
        assert isinstance(result.structuredContent["results"], list)

    asyncio.run(_with_session(check))


def test_client_get_prompt_interpolates_arguments() -> None:
    async def check(session: ClientSession) -> None:
        result = await session.get_prompt(
            "find_heritage_items",
            arguments={"topic": "dante", "iiif_only": "true"},
        )
        text = result.messages[0].content.text
        assert "dante" in text
        assert "has_iiif_manifest" in text

    asyncio.run(_with_session(check))
