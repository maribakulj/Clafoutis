"""Tests for per-source timeouts in SearchOrchestrator."""

import asyncio

from app.config.settings import settings
from app.connectors.base import BaseConnector
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchRequest, SearchResponse
from app.models.source_models import SourceCapabilities
from app.services.search_orchestrator import SearchOrchestrator


class _HangingConnector(BaseConnector):
    name = "hanging"
    label = "Hanging"
    source_type = "stub"

    async def search(self, query, filters, page, page_size):
        await asyncio.sleep(10)  # Longer than any reasonable test timeout
        raise AssertionError("should have timed out")

    async def get_item(self, source_item_id):
        return None

    async def resolve_manifest(self, item=None, record_url=None):
        return None

    async def healthcheck(self):
        return {"status": "ok"}

    async def capabilities(self):
        return SourceCapabilities()


def test_orchestrator_times_out_slow_source_without_stalling_peers(monkeypatch) -> None:
    monkeypatch.setattr(settings, "request_timeout_seconds", 0.2)

    registry = ConnectorRegistry()
    registry.register(MockConnector())
    registry.register(_HangingConnector())
    orchestrator = SearchOrchestrator(registry)

    response = asyncio.run(orchestrator.search(SearchRequest(query="book")))

    assert "mock" in response.sources_used
    assert "hanging" not in response.sources_used
    timeout_failures = [pf for pf in response.partial_failures if pf.source == "hanging"]
    assert timeout_failures
    assert timeout_failures[0].status == "error"
    assert timeout_failures[0].error == "timeout"


def test_orchestrator_returns_mock_results_when_peer_times_out(monkeypatch) -> None:
    monkeypatch.setattr(settings, "request_timeout_seconds", 0.2)

    registry = ConnectorRegistry()
    registry.register(MockConnector())
    registry.register(_HangingConnector())
    orchestrator = SearchOrchestrator(registry)

    response: SearchResponse = asyncio.run(
        orchestrator.search(SearchRequest(query="book"))
    )

    assert any(isinstance(item, NormalizedItem) for item in response.results)
