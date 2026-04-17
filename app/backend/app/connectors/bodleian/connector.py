"""Bodleian connector implementation."""

from __future__ import annotations

import logging
import time

from app.config.settings import settings
from app.connectors.base import BaseConnector, FixtureConnectorMixin
from app.connectors.bodleian.fixtures import FIXTURE_BODLEIAN_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.error_sanitizer import sanitize_error_message
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id

logger = logging.getLogger(__name__)


class BodleianConnector(FixtureConnectorMixin, BaseConnector):
    """Bodleian connector -- live API first, fixture fallback on error."""

    name = "bodleian"
    label = "Bodleian Libraries"
    source_type = "institution"

    _DEFAULT_INSTITUTION = "Bodleian Libraries"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        start = time.perf_counter()

        if settings.bodleian_use_fixtures:
            return self._fixture_search_response(query, page, page_size, start, partial=[])

        try:
            records = await self._fetch_live_search_records(query, page=page, page_size=page_size)
            items = [self._map_live_record(r, i) for i, r in enumerate(records)]
        except Exception as exc:
            logger.warning("Bodleian live search failed, using fixtures: %s", exc)
            partial = [PartialFailure(
                source=self.name, status="degraded",
                error=f"live_bodleian_unavailable: {sanitize_error_message(exc)}",
            )]
            return self._fixture_search_response(query, page, page_size, start, partial=partial)

        return self._build_search_response(
            query=query, page=page, page_size=page_size,
            items=items, partial_failures=[],
            needs_local_pagination=False, start_time=start,
        )

    def _fixture_search_response(
        self,
        query: str,
        page: int,
        page_size: int,
        start: float,
        partial: list[PartialFailure],
    ) -> SearchResponse:
        records = self._search_fixtures(query, FIXTURE_BODLEIAN_RECORDS)
        items = [
            self._map_fixture_record(r, i, default_institution=self._DEFAULT_INSTITUTION)
            for i, r in enumerate(records)
        ]
        return self._build_search_response(
            query=query, page=page, page_size=page_size,
            items=items, partial_failures=partial,
            needs_local_pagination=True, start_time=start,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        if not settings.bodleian_use_fixtures:
            try:
                record = await self._fetch_live_record(source_item_id)
                if record is not None:
                    return self._map_live_record(record, 0)
            except Exception as exc:
                logger.warning("Bodleian live get_item failed for %s: %s", source_item_id, exc)

        return self._get_fixture_item(
            source_item_id, FIXTURE_BODLEIAN_RECORDS,
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

        from_fixture = self._resolve_manifest_from_fixtures(source, FIXTURE_BODLEIAN_RECORDS)
        if from_fixture:
            return from_fixture

        if "/objects/" in source:
            object_id = source.rstrip("/").split("/objects/")[-1]
            return f"https://iiif.bodleian.ox.ac.uk/iiif/manifest/{object_id}.json"

        return None

    async def healthcheck(self) -> dict[str, str]:
        if settings.bodleian_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}
        try:
            async with build_async_client() as client:
                response = await client.get(settings.bodleian_api_base_url)
                if response.status_code >= 400:
                    return {"status": "error", "mode": "live"}
            return {"status": "ok", "mode": "live"}
        except Exception:
            return {"status": "error", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    async def _fetch_live_record(self, source_item_id: str) -> dict[str, object] | None:
        """Fetch a single Bodleian record by id via the item detail endpoint."""

        url = f"{settings.bodleian_api_base_url.rstrip('/')}/items/{source_item_id}"
        async with build_async_client() as client:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        return data if isinstance(data, dict) else None

    async def _fetch_live_search_records(
        self, query: str, *, page: int = 1, page_size: int = 24,
    ) -> list[dict[str, object]]:
        url = f"{settings.bodleian_api_base_url.rstrip('/')}/search"
        params: dict[str, str | int] = {
            "q": query,
            "limit": page_size,
            "offset": max(0, (page - 1) * page_size),
        }

        async with build_async_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("unexpected Bodleian response shape")
        results = data["results"]
        return [entry for entry in results if isinstance(entry, dict)]

    def _map_live_record(self, record: dict[str, object], index: int) -> NormalizedItem:
        source_item_id = str(record.get("id") or f"bodleian-live-{index}")
        manifest_url = self._str_or_none(record.get("manifest_url"))
        creators_raw = record.get("creators")
        creators = [str(v) for v in creators_raw] if isinstance(creators_raw, list) else []

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=str(record.get("title") or "Bodleian document"),
            creators=creators,
            date_display=self._str_or_none(record.get("date")),
            object_type=str(record.get("object_type") or "other"),
            institution=self._DEFAULT_INSTITUTION,
            thumbnail_url=self._str_or_none(record.get("thumbnail_url")),
            record_url=self._str_or_none(record.get("record_url")),
            manifest_url=manifest_url,
            has_iiif_manifest=manifest_url is not None,
            has_images=True,
            has_ocr=False,
            availability="public",
            relevance_score=max(0.0, 1.0 - (index * 0.01)),
            normalization_warnings=[],
        )
