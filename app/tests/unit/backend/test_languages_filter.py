"""Tests for the languages filter on SearchOrchestrator."""

import asyncio

from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchFilters, SearchRequest, SearchResponse
from app.models.source_models import SourceCapabilities
from app.services.search_orchestrator import SearchOrchestrator
from app.utils.ids import make_global_id


def _item(source: str, item_id: str, languages: list[str]) -> NormalizedItem:
    return NormalizedItem(
        id=make_global_id(source, item_id),
        source=source,
        source_label=source.title(),
        source_item_id=item_id,
        title=f"Item {item_id}",
        languages=languages,
    )


class _Stub(BaseConnector):
    name = "stub"
    label = "Stub"
    source_type = "stub"

    def __init__(self, items: list[NormalizedItem]) -> None:
        self._items = items

    async def search(self, query, filters, page, page_size):
        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total_estimated=len(self._items),
            results=self._items,
            sources_used=[self.name],
            partial_failures=[],
            duration_ms=1,
        )

    async def get_item(self, source_item_id):
        return None

    async def resolve_manifest(self, item=None, record_url=None):
        return None

    async def healthcheck(self):
        return {"status": "ok"}

    async def capabilities(self):
        return SourceCapabilities()


def test_languages_filter_keeps_intersecting_items() -> None:
    connector = _Stub(
        [
            _item("stub", "lat-only", ["lat"]),
            _item("stub", "fr-only", ["fre"]),
            _item("stub", "lat-fr", ["lat", "fre"]),
            _item("stub", "none", []),
        ]
    )
    registry = ConnectorRegistry()
    registry.register(connector)

    response = asyncio.run(
        SearchOrchestrator(registry).search(
            SearchRequest(query="q", filters=SearchFilters(languages=["lat"]))
        )
    )

    kept = {item.source_item_id for item in response.results}
    assert kept == {"lat-only", "lat-fr"}


def test_languages_filter_without_constraint_keeps_all() -> None:
    connector = _Stub(
        [
            _item("stub", "a", []),
            _item("stub", "b", ["eng"]),
        ]
    )
    registry = ConnectorRegistry()
    registry.register(connector)

    response = asyncio.run(SearchOrchestrator(registry).search(SearchRequest(query="q")))
    assert len(response.results) == 2
