"""Tests for ManifestResolver service."""

import asyncio

import pytest
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.models.manifest_models import ResolveManifestRequest
from app.services.manifest_resolver import ManifestResolver
from app.utils.errors import NotFoundError


def _make_resolver() -> ManifestResolver:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    return ManifestResolver(registry)


def test_resolve_returns_manifest_for_known_item() -> None:
    resolver = _make_resolver()
    request = ResolveManifestRequest(source="mock", source_item_id="ms-1")
    result = asyncio.run(resolver.resolve(request))
    assert result.status == "resolved"
    assert result.manifest_url is not None


def test_resolve_returns_not_found_for_item_without_manifest() -> None:
    resolver = _make_resolver()
    request = ResolveManifestRequest(source="mock", source_item_id="ms-2")
    result = asyncio.run(resolver.resolve(request))
    assert result.status == "not_found"
    assert result.manifest_url is None


def test_resolve_raises_for_unknown_source() -> None:
    resolver = _make_resolver()
    request = ResolveManifestRequest(source="unknown", source_item_id="x")
    with pytest.raises(NotFoundError, match="Unknown source"):
        asyncio.run(resolver.resolve(request))
