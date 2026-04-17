"""End-to-end test of the streamable-http MCP transport.

Launches ``clafoutis-mcp-http`` in a subprocess on a random port, waits
for it to accept connections, connects with the official MCP streamable
HTTP client, and exercises the same surface as the stdio roundtrip test.

Skipped when the ``mcp`` extra is not installed.
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time

import pytest

pytest.importorskip("mcp")
from mcp import ClientSession  # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for(host: str, port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError as err:
            last_err = err
            time.sleep(0.1)
    raise RuntimeError(f"MCP HTTP server did not start on {host}:{port}: {last_err!r}")


@pytest.fixture()
def http_server() -> subprocess.Popen:
    port = _free_port()
    env = os.environ.copy()
    env["CLAFOUTIS_MCP_HOST"] = "127.0.0.1"
    env["CLAFOUTIS_MCP_PORT"] = str(port)
    env["CLAFOUTIS_GALLICA_USE_FIXTURES"] = "true"
    env["CLAFOUTIS_BODLEIAN_USE_FIXTURES"] = "true"
    env["CLAFOUTIS_EUROPEANA_USE_FIXTURES"] = "true"
    process = subprocess.Popen(
        [sys.executable, "-c", "from app.mcp.server import run_http; run_http()"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for("127.0.0.1", port)
        process.port = port  # type: ignore[attr-defined]
        yield process
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def test_streamable_http_transport_roundtrip(http_server: subprocess.Popen) -> None:
    port = http_server.port  # type: ignore[attr-defined]

    async def check() -> None:
        endpoint = f"http://127.0.0.1:{port}/mcp"
        async with (
            streamablehttp_client(endpoint) as (read, write, _meta),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            tools = await session.list_tools()
            assert {t.name for t in tools.tools} >= {
                "search_items",
                "list_sources",
                "open_in_mirador",
            }

            sources = await session.list_resources()
            assert any(
                str(r.uri) == "clafoutis://sources" for r in sources.resources
            )

            result = await session.call_tool(
                "search_items", {"query": "book", "page_size": 3}
            )
            assert result.structuredContent is not None
            assert "results" in result.structuredContent

    asyncio.run(check())
