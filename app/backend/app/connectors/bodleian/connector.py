"""Bodleian connector implementation."""

from __future__ import annotations

import time

from app.config.settings import settings
from app.connectors.base import BaseConnector
from app.connectors.bodleian.fixtures import FIXTURE_BODLEIAN_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id


class BodleianConnector(BaseConnector):
    """Bodleian connector with fixture-first mode and optional live endpoint check."""

    name = "bodleian"
    label = "Bodleian Libraries"
    source_type = "institution"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Search Bodleian records and return normalized items."""

        start = time.perf_counter()
        partial_failures: list[PartialFailure]

        if settings.bodleian_use_fixtures:
            records = self._search_fixtures(query)
            items = [self._map_fixture_record(record, index) for index, record in enumerate(records)]
            partial_failures = [PartialFailure(source=self.name, status="ok")]
        else:
            try:
                records = await self._fetch_live_search_records(query)
                items = [self._map_live_record(record, index) for index, record in enumerate(records)]
                partial_failures = [PartialFailure(source=self.name, status="ok")]
            except Exception as exc:
                records = self._search_fixtures(query)
                items = [self._map_fixture_record(record, index) for index, record in enumerate(records)]
                partial_failures = [
                    PartialFailure(
                        source=self.name,
                        status="degraded",
                        error=f"live_bodleian_unavailable: {exc}",
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
            partial_failures=partial_failures,
            duration_ms=int((time.perf_counter() - start) * 1000),
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        """Get one Bodleian normalized item by source identifier."""

        for fixture in FIXTURE_BODLEIAN_RECORDS:
            if fixture["source_item_id"] == source_item_id:
                return self._map_fixture_record(fixture, 0)
        return None

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve Bodleian manifest from item or deterministic URL patterns."""

        if item and item.manifest_url:
            return item.manifest_url

        source = record_url or (item.record_url if item else None)
        if not source:
            return None

        for fixture in FIXTURE_BODLEIAN_RECORDS:
            if fixture.get("record_url") == source:
                return str(fixture.get("manifest_url"))

        if "/objects/" in source:
            object_id = source.rstrip("/").split("/objects/")[-1]
            return f"https://iiif.bodleian.ox.ac.uk/iiif/manifest/{object_id}.json"

        return None

    async def healthcheck(self) -> dict[str, str]:
        """Perform a lightweight Bodleian healthcheck."""

        if settings.bodleian_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}

        async with await build_async_client() as client:
            response = await client.get(settings.bodleian_api_base_url)
            if response.status_code >= 400:
                return {"status": "error", "mode": "live"}
        return {"status": "ok", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        """Return Bodleian connector capabilities."""

        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    async def _fetch_live_search_records(self, query: str) -> list[dict[str, object]]:
        """Fetch live Bodleian search records (best effort MVP endpoint)."""

        url = f"{settings.bodleian_api_base_url.rstrip('/')}/search"
        params = {"q": query, "limit": 24}

        async with await build_async_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict) or "results" not in data or not isinstance(data["results"], list):
            raise ValueError("unexpected Bodleian response shape")
        return data["results"]

    def _search_fixtures(self, query: str) -> list[dict[str, object]]:
        lowered = query.lower().strip()
        return [
            record
            for record in FIXTURE_BODLEIAN_RECORDS
            if lowered in str(record["title"]).lower() or lowered in " ".join(record.get("creators", [])).lower()
        ]

    def _map_live_record(self, record: dict[str, object], index: int) -> NormalizedItem:
        source_item_id = str(record.get("id") or f"bodleian-live-{index}")
        title = str(record.get("title") or "Bodleian document")
        creators_raw = record.get("creators") or []
        creators = [str(value) for value in creators_raw] if isinstance(creators_raw, list) else []
        date_display = str(record.get("date")) if record.get("date") else None
        record_url = str(record.get("record_url")) if record.get("record_url") else None
        manifest_url = str(record.get("manifest_url")) if record.get("manifest_url") else None

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=title,
            creators=creators,
            date_display=date_display,
            object_type=str(record.get("object_type") or "other"),
            institution="Bodleian Libraries",
            thumbnail_url=str(record.get("thumbnail_url")) if record.get("thumbnail_url") else None,
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
            institution=str(record.get("institution")) if record.get("institution") else "Bodleian Libraries",
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
