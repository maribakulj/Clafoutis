#!/usr/bin/env python
"""Minimal MCP client example.

Spawns the Clafoutis MCP server as a stdio subprocess, connects with the
official ``mcp`` client SDK, and exercises each surface (tools, resources,
prompts). Intended as a self-contained reference for downstream agents
and as a smoke test against local changes.

Usage::

    pip install -e '.[mcp]'
    python scripts/mcp_client_example.py
    python scripts/mcp_client_example.py --query "dante"

The script writes to stderr when appropriate and prints structured
results on stdout so it can be piped into jq or another tool.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Make `app` importable when running from the repo root without pip install.
sys.path.append(str(Path(__file__).resolve().parents[1] / "app" / "backend"))

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def _content_payload(result: Any) -> Any:
    """Return structured content when available, otherwise the raw text blocks."""

    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    return [getattr(item, "text", repr(item)) for item in result.content]


async def run(query: str) -> int:
    """Connect to the server and dump one example per MCP surface."""

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        env=None,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("# Available tools")
            tools = await session.list_tools()
            for tool in tools.tools:
                ann = tool.annotations
                read_only = getattr(ann, "readOnlyHint", None) if ann else None
                print(f"- {tool.name} (readOnly={read_only})")

            print("\n# Resources")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"- {resource.uri} — {resource.name}")

            print("\n# Prompts")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"- {prompt.name}")

            print("\n# Reading clafoutis://sources")
            sources_content = await session.read_resource("clafoutis://sources")
            for block in sources_content.contents:
                text = getattr(block, "text", None)
                if text:
                    data = json.loads(text)
                    names = [s["name"] for s in data.get("sources", [])]
                    print(f"  registered sources: {names}")

            print(f"\n# Calling search_items(query={query!r})")
            result = await session.call_tool(
                "search_items", {"query": query, "page_size": 3}
            )
            payload = _content_payload(result)
            if isinstance(payload, dict):
                items = payload.get("results", [])
                print(f"  {len(items)} results, first titles:")
                for item in items[:3]:
                    print(f"    - {item.get('title')!r} ({item.get('source')})")
            else:
                print(f"  text-only response: {payload[:2]}")

            print("\n# Calling open_in_mirador with a known manifest")
            open_result = await session.call_tool(
                "open_in_mirador",
                {
                    "manifest_urls": [
                        "https://gallica.bnf.fr/iiif/ark:/12148/x/manifest.json"
                    ]
                },
            )
            open_payload = _content_payload(open_result)
            if isinstance(open_payload, dict):
                print(
                    "  manifest_urls:", open_payload.get("manifest_urls"),
                )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="book", help="Search query to run")
    args = parser.parse_args()
    return asyncio.run(run(args.query))


if __name__ == "__main__":
    sys.exit(main())
