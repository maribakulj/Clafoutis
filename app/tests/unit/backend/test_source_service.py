"""Tests for SourceService."""

import asyncio

from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.services.source_service import SourceService


def test_list_sources_returns_registered_connectors() -> None:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    service = SourceService(registry)

    result = asyncio.run(service.list_sources())

    assert len(result.sources) == 1
    assert result.sources[0].name == "mock"
    assert result.sources[0].healthy is True
    assert result.sources[0].capabilities.search is True
