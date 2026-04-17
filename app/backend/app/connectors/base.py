"""Abstract connector interface for all external sources."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.ids import make_global_id

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Common contract implemented by every source connector."""

    name: str
    label: str
    source_type: str

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Execute source search and return normalized results."""

    @abstractmethod
    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        """Get a single normalized item by source-specific identifier."""

    @abstractmethod
    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve a IIIF manifest URL from item metadata or record URL."""

    @abstractmethod
    async def healthcheck(self) -> dict[str, str]:
        """Check connector health and return a compact status report."""

    @abstractmethod
    async def capabilities(self) -> SourceCapabilities:
        """Declare static connector capabilities."""

    async def find_by_record_url(self, record_url: str) -> NormalizedItem | None:
        """Return the matching item for a record URL, if the source recognizes it.

        Default: the connector does not index record URLs. Sources with a
        finite catalog (mock, fixtures) may override this to enrich import
        responses with a full NormalizedItem.
        """

        return None


class FixtureConnectorMixin:
    """Shared helpers for connectors that use fixture fallback."""

    name: str
    label: str

    def _search_fixtures(
        self,
        query: str,
        fixtures: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Filter fixture records by query substring match on title/creators."""
        lowered = query.lower().strip()

        def _creators_text(raw: object) -> str:
            if isinstance(raw, list):
                return " ".join(str(item) for item in raw).lower()
            if isinstance(raw, str):
                return raw.lower()
            return ""

        return [
            record
            for record in fixtures
            if lowered in str(record.get("title", "")).lower()
            or lowered in _creators_text(record.get("creators"))
        ]

    def _map_fixture_record(
        self,
        fixture: dict[str, object],
        index: int,
        *,
        default_institution: str | None = None,
        manifest_url_override: str | None = None,
    ) -> NormalizedItem:
        """Map a fixture dict to a NormalizedItem with shared logic."""
        source_item_id = str(fixture["source_item_id"])
        manifest_url = manifest_url_override or (
            str(fixture.get("manifest_url")) if fixture.get("manifest_url") else None
        )
        raw_creators = fixture.get("creators", [])
        creators_list = raw_creators if isinstance(raw_creators, list) else []
        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=str(fixture["title"]),
            creators=[str(v) for v in creators_list],
            date_display=str(fixture.get("date_display")) if fixture.get("date_display") else None,
            object_type=str(fixture.get("object_type", "other")),
            institution=(
                str(fixture.get("institution"))
                if fixture.get("institution")
                else default_institution
            ),
            thumbnail_url=str(fixture.get("thumbnail_url")) if fixture.get("thumbnail_url") else None,
            record_url=str(fixture.get("record_url")) if fixture.get("record_url") else None,
            manifest_url=manifest_url,
            has_iiif_manifest=manifest_url is not None,
            has_images=True,
            has_ocr=False,
            availability="public",
            relevance_score=max(0.0, 1.0 - (index * 0.01)),
            normalization_warnings=["fixture_mode"],
        )

    def _build_search_response(
        self,
        *,
        query: str,
        page: int,
        page_size: int,
        items: list[NormalizedItem],
        partial_failures: list[PartialFailure],
        needs_local_pagination: bool,
        start_time: float,
    ) -> SearchResponse:
        """Build SearchResponse with optional local pagination."""
        total = len(items)
        if needs_local_pagination:
            start_index = (page - 1) * page_size
            page_items = items[start_index : start_index + page_size]
            has_next = start_index + page_size < total
        else:
            page_items = items
            # Live mode: the source already applied pagination, so we can only
            # heuristically say "maybe more if it filled the page".
            has_next = len(page_items) >= page_size

        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total_estimated=total,
            has_next_page=has_next,
            results=page_items,
            sources_used=[self.name],
            partial_failures=partial_failures,
            duration_ms=int((time.perf_counter() - start_time) * 1000),
        )

    def _get_fixture_item(
        self,
        source_item_id: str,
        fixtures: list[dict[str, object]],
        *,
        default_institution: str | None = None,
        manifest_url_override: str | None = None,
    ) -> NormalizedItem | None:
        """Lookup a single item from fixtures by source_item_id."""
        for fixture in fixtures:
            if fixture["source_item_id"] == source_item_id:
                return self._map_fixture_record(
                    fixture,
                    0,
                    default_institution=default_institution,
                    manifest_url_override=manifest_url_override,
                )
        return None

    def _resolve_manifest_from_fixtures(
        self,
        record_url: str,
        fixtures: list[dict[str, object]],
    ) -> str | None:
        """Try to resolve manifest URL from fixture data."""
        for fixture in fixtures:
            if fixture.get("record_url") == record_url:
                manifest = fixture.get("manifest_url")
                return str(manifest) if manifest else None
        return None

    @staticmethod
    def _str_or_none(value: object) -> str | None:
        """Convert to string or return None if falsy."""
        return str(value) if value else None
