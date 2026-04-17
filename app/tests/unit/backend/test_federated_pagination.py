"""Regression tests for federated pagination in SearchOrchestrator."""

import asyncio

from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchRequest, SearchResponse
from app.models.source_models import SourceCapabilities
from app.services.search_orchestrator import SearchOrchestrator
from app.utils.ids import make_global_id


class _StubConnector(BaseConnector):
    def __init__(
        self,
        name: str,
        *,
        items_per_page: int,
        total: int,
    ) -> None:
        self.name = name
        self.label = name.title()
        self.source_type = "stub"
        self._items_per_page = items_per_page
        self._total = total

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        start = (page - 1) * page_size
        end = min(start + page_size, self._total)
        results = [
            NormalizedItem(
                id=make_global_id(self.name, f"{self.name}-{i}"),
                source=self.name,
                source_label=self.label,
                source_item_id=f"{self.name}-{i}",
                title=f"Item {i}",
                relevance_score=1.0 - (i * 0.01),
            )
            for i in range(start, end)
        ]
        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total_estimated=self._total,
            has_next_page=end < self._total,
            results=results,
            sources_used=[self.name],
            partial_failures=[],
            duration_ms=1,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        return None

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        return None

    async def healthcheck(self) -> dict[str, str]:
        return {"status": "ok"}

    async def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities()


def _make_orchestrator(*connectors: BaseConnector) -> SearchOrchestrator:
    registry = ConnectorRegistry()
    for connector in connectors:
        registry.register(connector)
    return SearchOrchestrator(registry)


def test_orchestrator_preserves_full_page_from_each_source() -> None:
    """Each source's page_size items must survive the merge (no silent drop)."""

    orchestrator = _make_orchestrator(
        _StubConnector("alpha", items_per_page=5, total=50),
        _StubConnector("beta", items_per_page=5, total=50),
    )

    response = asyncio.run(
        orchestrator.search(SearchRequest(query="q", page=1, page_size=5))
    )

    # Both sources returned 5 results each; the orchestrator must surface all 10
    # in the response (previously it re-paginated and kept only 5).
    assert len(response.results) == 10


def test_orchestrator_reports_has_next_page_when_any_source_has_more() -> None:
    orchestrator = _make_orchestrator(
        _StubConnector("alpha", items_per_page=5, total=5),
        _StubConnector("beta", items_per_page=5, total=100),
    )

    response = asyncio.run(
        orchestrator.search(SearchRequest(query="q", page=1, page_size=5))
    )

    assert response.has_next_page is True


def test_orchestrator_has_next_page_false_when_no_source_has_more() -> None:
    orchestrator = _make_orchestrator(
        _StubConnector("alpha", items_per_page=5, total=3),
        _StubConnector("beta", items_per_page=5, total=4),
    )

    response = asyncio.run(
        orchestrator.search(SearchRequest(query="q", page=1, page_size=5))
    )

    assert response.has_next_page is False


def test_orchestrator_aggregates_total_estimated() -> None:
    orchestrator = _make_orchestrator(
        _StubConnector("alpha", items_per_page=5, total=42),
        _StubConnector("beta", items_per_page=5, total=8),
    )

    response = asyncio.run(
        orchestrator.search(SearchRequest(query="q", page=1, page_size=5))
    )

    assert response.total_estimated == 50
