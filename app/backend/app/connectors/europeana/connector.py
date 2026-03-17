"""Europeana connector implementation."""

from __future__ import annotations

import time

from app.config.settings import settings
from app.connectors.base import BaseConnector
from app.connectors.europeana.fixtures import FIXTURE_EUROPEANA_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id


class EuropeanaConnector(BaseConnector):
    """Europeana connector with fixture-first strategy and optional live API mode."""

    name = "europeana"
    label = "Europeana"
    source_type = "institution"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Search Europeana and map results to normalized items."""

        start = time.perf_counter()

        if settings.europeana_use_fixtures:
            records = self._search_fixtures(query)
            items = [self._map_fixture_record(record, index) for index, record in enumerate(records)]
            partial = [PartialFailure(source=self.name, status="ok")]
        else:
            try:
                records = await self._fetch_live_search_records(query=query, page=page, page_size=page_size)
                items = [self._map_live_record(record, index) for index, record in enumerate(records)]
                partial = [PartialFailure(source=self.name, status="ok")]
            except Exception as exc:
                records = self._search_fixtures(query)
                items = [self._map_fixture_record(record, index) for index, record in enumerate(records)]
                partial = [
                    PartialFailure(
                        source=self.name,
                        status="degraded",
                        error=f"live_europeana_unavailable: {exc}",
                    )
                ]

        start_index = (page - 1) * page_size
        page_items = items[start_index : start_index + page_size]

        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total_estimated=len(items),
            results=page_items,
            sources_used=[self.name],
            partial_failures=partial,
            duration_ms=int((time.perf_counter() - start) * 1000),
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        """Get one Europeana normalized item by source identifier."""

        for fixture in FIXTURE_EUROPEANA_RECORDS:
            if fixture["source_item_id"] == source_item_id:
                return self._map_fixture_record(fixture, 0)
        return None

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve Europeana manifest from normalized item or record URL."""

        if item and item.manifest_url:
            return item.manifest_url

        source = record_url or (item.record_url if item else None)
        if not source:
            return None

        for fixture in FIXTURE_EUROPEANA_RECORDS:
            if fixture.get("record_url") == source:
                return str(fixture.get("manifest_url"))

        if "/item/" in source:
            item_path = source.split("/item/", maxsplit=1)[-1].strip("/")
            return f"https://iiif.europeana.eu/presentation/{item_path}/manifest"

        return None

    async def healthcheck(self) -> dict[str, str]:
        """Perform a lightweight Europeana healthcheck."""

        if settings.europeana_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}

        if not settings.europeana_api_key:
            return {"status": "error", "mode": "live", "reason": "missing_api_key"}

        async with await build_async_client() as client:
            response = await client.get(settings.europeana_api_base_url)
            if response.status_code >= 400:
                return {"status": "error", "mode": "live"}
        return {"status": "ok", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        """Return Europeana connector capabilities."""

        return SourceCapabilities(
            search=True,
            get_item=True,
            resolve_manifest=True,
            free_text_search=True,
            structured_search=True,
            pagination=True,
            facets=False,
            direct_manifest_resolution=True,
            thumbnails=True,
            ocr_signal=False,
            image_availability=True,
            runtime_detection=False,
            protocol_family="proprietary",
        )

    async def _fetch_live_search_records(
        self,
        query: str,
        page: int,
        page_size: int,
    ) -> list[dict[str, object]]:
        """Fetch live Europeana search results via Record Search API."""

        if not settings.europeana_api_key:
            raise RuntimeError("missing europeana api key")

        params = {
            "wskey": settings.europeana_api_key,
            "query": query,
            "rows": page_size,
            "start": ((page - 1) * page_size) + 1,
            "profile": "rich",
        }

        async with await build_async_client() as client:
            response = await client.get(settings.europeana_api_base_url, params=params)
            response.raise_for_status()
            data = response.json()

        items = data.get("items")
        if not isinstance(items, list):
            raise ValueError("unexpected Europeana response shape")
        return items

    def _search_fixtures(self, query: str) -> list[dict[str, object]]:
        lowered = query.lower().strip()
        return [
            record
            for record in FIXTURE_EUROPEANA_RECORDS
            if lowered in str(record["title"]).lower() or lowered in " ".join(record.get("creators", [])).lower()
        ]

    def _map_live_record(self, record: dict[str, object], index: int) -> NormalizedItem:
        source_item_id = str(record.get("id") or f"europeana-live-{index}")

        title = self._first_text(record.get("title"), default="Europeana document")
        creators = self._list_text(record.get("dcCreator"))
        date_display = self._first_text(record.get("timestamp_created_epoch"), default=None)
        record_url = str(record.get("guid")) if record.get("guid") else None

        edm_is_shown_by = self._first_text(record.get("edmIsShownBy"), default=None)
        manifest_url = edm_is_shown_by if edm_is_shown_by and "manifest" in edm_is_shown_by else None
        if manifest_url is None and record_url and "/item/" in record_url:
            item_path = record_url.split("/item/", maxsplit=1)[-1].strip("/")
            manifest_url = f"https://iiif.europeana.eu/presentation/{item_path}/manifest"

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=title,
            creators=creators,
            date_display=date_display,
            object_type="other",
            institution="Europeana",
            thumbnail_url=self._first_text(record.get("edmPreview"), default=None),
            record_url=record_url,
            manifest_url=manifest_url,
            has_iiif_manifest=manifest_url is not None,
            has_images=True,
            has_ocr=False,
            availability="public",
            relevance_score=max(0.0, 1.0 - (index * 0.01)),
            normalization_warnings=[],
        )

    def _map_fixture_record(self, record: dict[str, object], index: int) -> NormalizedItem:
        source_item_id = str(record["source_item_id"])
        manifest_url = str(record.get("manifest_url")) if record.get("manifest_url") else None

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=str(record["title"]),
            creators=[str(value) for value in record.get("creators", [])],
            date_display=str(record.get("date_display")) if record.get("date_display") else None,
            object_type=str(record.get("object_type") or "other"),
            institution=str(record.get("institution")) if record.get("institution") else "Europeana",
            thumbnail_url=str(record.get("thumbnail_url")) if record.get("thumbnail_url") else None,
            record_url=str(record.get("record_url")) if record.get("record_url") else None,
            manifest_url=manifest_url,
            has_iiif_manifest=manifest_url is not None,
            has_images=True,
            has_ocr=False,
            availability="public",
            relevance_score=max(0.0, 1.0 - (index * 0.01)),
            normalization_warnings=["fixture_mode"],
        )

    def _first_text(self, value: object, default: str | None) -> str | None:
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str):
            return value
        return default

    def _list_text(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(entry) for entry in value]
        if isinstance(value, str):
            return [value]
        return []
