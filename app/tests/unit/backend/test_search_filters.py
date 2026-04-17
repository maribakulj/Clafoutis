"""Tests for typed SearchFilters applied by the orchestrator."""

import asyncio

from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import (
    SearchFilters,
    SearchRequest,
    SearchResponse,
)
from app.models.source_models import SourceCapabilities
from app.services.search_orchestrator import SearchOrchestrator
from app.utils.ids import make_global_id


class _CatalogConnector(BaseConnector):
    name = "catalog"
    label = "Catalog"
    source_type = "stub"

    def __init__(self) -> None:
        self._items = [
            NormalizedItem(
                id=make_global_id(self.name, "book-1"),
                source=self.name,
                source_label=self.label,
                source_item_id="book-1",
                title="Book with manifest",
                object_type="book",
                has_iiif_manifest=True,
                manifest_url="https://example.org/1/manifest",
                relevance_score=0.9,
            ),
            NormalizedItem(
                id=make_global_id(self.name, "map-1"),
                source=self.name,
                source_label=self.label,
                source_item_id="map-1",
                title="Map without manifest",
                object_type="map",
                has_iiif_manifest=False,
                relevance_score=0.8,
            ),
            NormalizedItem(
                id=make_global_id(self.name, "ms-1"),
                source=self.name,
                source_label=self.label,
                source_item_id="ms-1",
                title="Manuscript with manifest",
                object_type="manuscript",
                has_iiif_manifest=True,
                manifest_url="https://example.org/2/manifest",
                relevance_score=0.7,
            ),
        ]

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
        return next((i for i in self._items if i.source_item_id == source_item_id), None)

    async def resolve_manifest(self, item=None, record_url=None):
        return item.manifest_url if item else None

    async def healthcheck(self):
        return {"status": "ok"}

    async def capabilities(self):
        return SourceCapabilities()


def _orchestrator() -> SearchOrchestrator:
    registry = ConnectorRegistry()
    registry.register(_CatalogConnector())
    return SearchOrchestrator(registry)


def test_filter_has_iiif_manifest_true_keeps_only_manifested() -> None:
    response = asyncio.run(
        _orchestrator().search(
            SearchRequest(query="q", filters=SearchFilters(has_iiif_manifest=True))
        )
    )
    assert {item.source_item_id for item in response.results} == {"book-1", "ms-1"}


def test_filter_has_iiif_manifest_false_keeps_only_non_manifested() -> None:
    response = asyncio.run(
        _orchestrator().search(
            SearchRequest(query="q", filters=SearchFilters(has_iiif_manifest=False))
        )
    )
    assert {item.source_item_id for item in response.results} == {"map-1"}


def test_filter_object_type_restricts_to_list() -> None:
    response = asyncio.run(
        _orchestrator().search(
            SearchRequest(
                query="q", filters=SearchFilters(object_type=["book", "manuscript"])
            )
        )
    )
    assert {item.object_type for item in response.results} == {"book", "manuscript"}


def test_default_filters_keep_everything() -> None:
    response = asyncio.run(_orchestrator().search(SearchRequest(query="q")))
    assert len(response.results) == 3
