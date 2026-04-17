"""Tests for ranking bonus and weak deduplication in SearchOrchestrator."""

import asyncio

from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchRequest, SearchResponse
from app.models.source_models import SourceCapabilities
from app.services.search_orchestrator import SearchOrchestrator
from app.utils.ids import make_global_id


def _item(
    *,
    source: str,
    item_id: str,
    title: str,
    score: float = 0.5,
    manifest: str | None = None,
    thumbnail: str | None = None,
    date: str | None = None,
) -> NormalizedItem:
    return NormalizedItem(
        id=make_global_id(source, item_id),
        source=source,
        source_label=source.title(),
        source_item_id=item_id,
        title=title,
        manifest_url=manifest,
        has_iiif_manifest=manifest is not None,
        thumbnail_url=thumbnail,
        date_display=date,
        relevance_score=score,
    )


class _FixedConnector(BaseConnector):
    source_type = "stub"

    def __init__(self, name: str, items: list[NormalizedItem]) -> None:
        self.name = name
        self.label = name.title()
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
        return next((i for i in self._items if i.source_item_id == source_item_id), None)

    async def resolve_manifest(self, item=None, record_url=None):
        return None

    async def healthcheck(self):
        return {"status": "ok"}

    async def capabilities(self):
        return SourceCapabilities()


def _orchestrator(*connectors: BaseConnector) -> SearchOrchestrator:
    registry = ConnectorRegistry()
    for connector in connectors:
        registry.register(connector)
    return SearchOrchestrator(registry)


def test_items_sharing_manifest_url_are_deduplicated() -> None:
    shared = "https://example.org/m/manifest"
    a = _FixedConnector("a", [_item(source="a", item_id="1", title="X", manifest=shared, score=0.9)])
    b = _FixedConnector("b", [_item(source="b", item_id="2", title="X (copy)", manifest=shared, score=0.4)])

    response = asyncio.run(_orchestrator(a, b).search(SearchRequest(query="q")))
    # Only one item kept; the higher-ranked one survives.
    assert len(response.results) == 1
    assert response.results[0].source == "a"


def test_items_with_same_normalized_title_and_date_are_weakly_deduplicated() -> None:
    a = _FixedConnector(
        "a",
        [_item(source="a", item_id="1", title="La Divine Comédie", date="1898", score=0.9)],
    )
    b = _FixedConnector(
        "b",
        [_item(source="b", item_id="2", title="La  divine  comedie!!", date="1898", score=0.3)],
    )

    response = asyncio.run(_orchestrator(a, b).search(SearchRequest(query="q")))
    assert len(response.results) == 1


def test_items_with_same_title_but_different_dates_are_kept() -> None:
    a = _FixedConnector(
        "a",
        [_item(source="a", item_id="1", title="Book of Hours", date="1450", score=0.9)],
    )
    b = _FixedConnector(
        "b",
        [_item(source="b", item_id="2", title="Book of Hours", date="1500", score=0.8)],
    )

    response = asyncio.run(_orchestrator(a, b).search(SearchRequest(query="q")))
    assert len(response.results) == 2


def test_completeness_bonus_promotes_manifested_item_over_bare_one() -> None:
    # Two items with identical native scores; the one with manifest+thumbnail
    # must rank first thanks to the completeness bonus.
    a = _FixedConnector(
        "a",
        [
            _item(source="a", item_id="plain", title="A", score=0.6),
            _item(
                source="a",
                item_id="rich",
                title="B",
                score=0.6,
                manifest="https://example.org/rich/manifest",
                thumbnail="https://example.org/rich.jpg",
            ),
        ],
    )
    response = asyncio.run(_orchestrator(a).search(SearchRequest(query="q")))
    assert [r.source_item_id for r in response.results] == ["rich", "plain"]


def test_dedup_preserves_order_after_reranking() -> None:
    shared = "https://example.org/m/manifest"
    a = _FixedConnector("a", [_item(source="a", item_id="1", title="X", manifest=shared, score=0.2)])
    b = _FixedConnector(
        "b",
        [_item(source="b", item_id="2", title="X", manifest=shared, score=0.2, thumbnail="t")],
    )
    # Even though the native scores are equal, the completeness bonus should
    # put source "b" first; the single survivor must therefore be "b".
    response = asyncio.run(_orchestrator(a, b).search(SearchRequest(query="q")))
    assert len(response.results) == 1
    assert response.results[0].source == "b"
