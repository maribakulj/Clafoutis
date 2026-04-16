"""Europeana connector implementation."""

from __future__ import annotations

import time

from app.config.settings import settings
from app.connectors.base import BaseConnector, FixtureConnectorMixin
from app.connectors.europeana.fixtures import FIXTURE_EUROPEANA_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id


class EuropeanaConnector(FixtureConnectorMixin, BaseConnector):
    """Europeana connector with fixture-first strategy and optional live API mode."""

    name = "europeana"
    label = "Europeana"
    source_type = "institution"

    _DEFAULT_INSTITUTION = "Europeana"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        start = time.perf_counter()
        needs_local_pagination = False

        if settings.europeana_use_fixtures:
            needs_local_pagination = True
            records = self._search_fixtures(query, FIXTURE_EUROPEANA_RECORDS)
            items = [
                self._map_fixture_record(r, i, default_institution=self._DEFAULT_INSTITUTION)
                for i, r in enumerate(records)
            ]
            partial = [PartialFailure(source=self.name, status="ok")]
        else:
            try:
                records = await self._fetch_live_search_records(query=query, page=page, page_size=page_size)
                items = [self._map_live_record(r, i) for i, r in enumerate(records)]
                partial = [PartialFailure(source=self.name, status="ok")]
            except Exception as exc:
                needs_local_pagination = True
                records = self._search_fixtures(query, FIXTURE_EUROPEANA_RECORDS)
                items = [
                    self._map_fixture_record(r, i, default_institution=self._DEFAULT_INSTITUTION)
                    for i, r in enumerate(records)
                ]
                partial = [PartialFailure(
                    source=self.name, status="degraded",
                    error=f"live_europeana_unavailable: {exc}",
                )]

        return self._build_search_response(
            query=query, page=page, page_size=page_size,
            items=items, partial_failures=partial,
            needs_local_pagination=needs_local_pagination, start_time=start,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        return self._get_fixture_item(
            source_item_id, FIXTURE_EUROPEANA_RECORDS,
            default_institution=self._DEFAULT_INSTITUTION,
        )

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        if item and item.manifest_url:
            return item.manifest_url

        source = record_url or (item.record_url if item else None)
        if not source:
            return None

        from_fixture = self._resolve_manifest_from_fixtures(source, FIXTURE_EUROPEANA_RECORDS)
        if from_fixture:
            return from_fixture

        if "/item/" in source:
            item_path = source.split("/item/", maxsplit=1)[-1].strip("/")
            return f"https://iiif.europeana.eu/presentation/{item_path}/manifest"

        return None

    async def healthcheck(self) -> dict[str, str]:
        if settings.europeana_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}
        if not settings.europeana_api_key:
            return {"status": "error", "mode": "live", "reason": "missing_api_key"}

        async with build_async_client() as client:
            response = await client.get(settings.europeana_api_base_url)
            if response.status_code >= 400:
                return {"status": "error", "mode": "live"}
        return {"status": "ok", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    async def _fetch_live_search_records(
        self, query: str, page: int, page_size: int,
    ) -> list[dict[str, object]]:
        if not settings.europeana_api_key:
            raise RuntimeError("missing europeana api key")

        params = {
            "wskey": settings.europeana_api_key,
            "query": query,
            "rows": page_size,
            "start": ((page - 1) * page_size) + 1,
            "profile": "rich",
        }

        async with build_async_client() as client:
            response = await client.get(settings.europeana_api_base_url, params=params)
            response.raise_for_status()
            data = response.json()

        items = data.get("items")
        if not isinstance(items, list):
            raise ValueError("unexpected Europeana response shape")
        return items

    def _map_live_record(self, record: dict[str, object], index: int) -> NormalizedItem:
        source_item_id = str(record.get("id") or f"europeana-live-{index}")
        record_url = self._str_or_none(record.get("guid"))

        edm = self._first_text(record.get("edmIsShownBy"), default=None)
        manifest_url = edm if edm and "manifest" in edm else None
        if manifest_url is None and record_url and "/item/" in record_url:
            item_path = record_url.split("/item/", maxsplit=1)[-1].strip("/")
            manifest_url = f"https://iiif.europeana.eu/presentation/{item_path}/manifest"

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=self._first_text(record.get("title"), default="Europeana document") or "",
            creators=self._list_text(record.get("dcCreator")),
            date_display=self._first_text(record.get("timestamp_created_epoch"), default=None),
            object_type="other",
            institution=self._DEFAULT_INSTITUTION,
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

    @staticmethod
    def _first_text(value: object, default: str | None) -> str | None:
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str):
            return value
        return default

    @staticmethod
    def _list_text(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(entry) for entry in value]
        if isinstance(value, str):
            return [value]
        return []
