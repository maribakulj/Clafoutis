import asyncio

from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.models.search_models import SearchRequest
from app.services.search_orchestrator import SearchOrchestrator


def test_search_orchestrator_returns_normalized_results() -> None:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    orchestrator = SearchOrchestrator(registry)

    response = asyncio.run(orchestrator.search(SearchRequest(query="book")))

    assert response.results
    assert response.results[0].id.startswith("mock:")
    assert response.sources_used == ["mock"]


def test_search_orchestrator_reports_unknown_source_as_partial_failure() -> None:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    orchestrator = SearchOrchestrator(registry)

    response = asyncio.run(orchestrator.search(SearchRequest(query="book", sources=["unknown"])))

    assert response.results == []
    assert response.sources_used == []
    assert response.partial_failures
    assert response.partial_failures[0].source == "unknown"
    assert response.partial_failures[0].status == "error"
