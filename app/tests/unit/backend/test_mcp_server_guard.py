"""Test that build_server fails gracefully when the mcp extra is missing."""

import builtins

import pytest
from app.mcp import server as mcp_server_module


def test_build_server_raises_clear_error_without_mcp_sdk(monkeypatch) -> None:
    """When the mcp package is unavailable, ``build_server`` must surface a
    helpful error pointing to the optional extra rather than a bare ImportError.
    """

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "mcp.server.fastmcp" or name.startswith("mcp.server"):
            raise ImportError("mcp not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match=r"\[mcp\]"):
        mcp_server_module.build_server()
