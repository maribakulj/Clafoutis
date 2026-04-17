#!/usr/bin/env python
"""Launch the Clafoutis MCP server over stdio.

Usage::

    pip install -e '.[mcp]'
    python scripts/run_mcp.py

For desktop MCP clients (e.g. Claude Desktop), register this script as a
stdio command. The server reuses the same backend services as the REST
API, so both surfaces behave identically.
"""

from pathlib import Path
import sys

# Make `app` importable when running from the repo root without `pip install`.
sys.path.append(str(Path(__file__).resolve().parents[1] / "app" / "backend"))

from app.mcp.server import run_stdio  # noqa: E402


if __name__ == "__main__":
    run_stdio()
