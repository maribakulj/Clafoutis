"""Europeana connector implementation."""

from __future__ import annotations

import logging
import time

from app.config.settings import settings
from app.connectors.base import BaseConnector, FixtureConnectorMixin
from app.connectors.europeana.fixtures import FIXTURE_EUROPEANA_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.error_sanitizer import sanitize_error_message
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id

logger = logging.getLogger(__name__)


class EuropeanaConnector(FixtureConnectorMixin, BaseConnector):
    """Europeana connector -- live API first, fixture fallback on error."""

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

        if settings.europeana_use_fixtures:
            return self._fixture_search_response(query, page, page_size, start, partial=[])

        try:
            records = await self._fetch_live_search_records(query=query, page=page, page_size=page_size)
            items = [self._map_live_record(r, i) for i, r in enumerate(records)]
        except Exception as exc:
            logger.warning("Europeana live search failed, using fixtures: %s", exc)
            partial = [PartialFailure(
                source=self.name, status="degraded",
                error=f"live_europeana_unavailable: {sanitize_error_message(exc)}",
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
        records = self._search_fixtures(query, FIXTURE_EUROPEANA_RECORDS)
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
        if not settings.europeana_use_fixtures and settings.europeana_api_key:
            try:
                record = await self._fetch_live_record(source_item_id)
                if record is not None:
                    return self._map_live_record(record, 0)
            except Exception as exc:
                logger.warning(
                    "Europeana live get_item failed for %s: %s", source_item_id, exc
                )
        return self._get_fixture_item(
            source_item_id, FIXTURE_EUROPEANA_RECORDS,
            default_institution=self._DEFAULT_INSTITUTION,
        )

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve a manifest URL with conservative heuristics.

        We do not fabricate a ``iiif.europeana.eu/presentation/.../manifest``
        URL from any arbitrary record URL: many Europeana records have no
        IIIF manifest and the UI would surface a 404. A manifest is only
        returned when (a) the item already carries one, (b) the fixture
        catalog resolves it, or (c) the source URL itself looks like a
        manifest endpoint.
        """

        if item and item.manifest_url:
            return item.manifest_url

        source = record_url or (item.record_url if item else None)
        if not source:
            return None

        from_fixture = self._resolve_manifest_from_fixtures(source, FIXTURE_EUROPEANA_RECORDS)
        if from_fixture:
            return from_fixture

        if "/presentation/" in source and source.endswith("/manifest"):
            return source

        return None

    async def healthcheck(self) -> dict[str, str]:
        if settings.europeana_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}
        if not settings.europeana_api_key:
            return {"status": "error", "mode": "live", "reason": "missing_api_key"}

        try:
            async with build_async_client() as client:
                response = await client.get(settings.europeana_api_base_url)
                if response.status_code >= 400:
                    return {"status": "error", "mode": "live"}
            return {"status": "ok", "mode": "live"}
        except Exception:
            return {"status": "error", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    async def _fetch_live_record(self, source_item_id: str) -> dict[str, object] | None:
        """Fetch a single record via Europeana Record v2 API."""

        normalized_id = source_item_id.lstrip("/")
        url = f"https://api.europeana.eu/record/v2/{normalized_id}.json"
        params = {"wskey": settings.europeana_api_key}
        async with build_async_client() as client:
            response = await client.get(url, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        obj = data.get("object") if isinstance(data, dict) else None
        return obj if isinstance(obj, dict) else None

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

        # Only accept an explicit manifest URL from the source. "manifest" as a
        # substring of edmIsShownBy (often a direct image URL) is not reliable,
        # and fabricating an iiif.europeana.eu URL for records without a real
        # manifest causes 404s in the reader.
        manifest_url = self._detect_manifest_url(record)

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=self._first_text(record.get("title"), default="Europeana document") or "",
            creators=self._list_text(record.get("dcCreator")),
            date_display=self._extract_date_display(record),
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

    @classmethod
    def _detect_manifest_url(cls, record: dict[str, object]) -> str | None:
        """Return a IIIF manifest URL if one is explicitly advertised."""

        # Some Europeana profiles expose a dedicated iiifManifest field.
        for key in ("iiifManifest", "dctermsIsReferencedBy"):
            candidate = cls._first_text(record.get(key), default=None)
            if candidate and "/manifest" in candidate and candidate.startswith("http"):
                return candidate
        edm = cls._first_text(record.get("edmIsShownBy"), default=None)
        if edm and edm.endswith("/manifest"):
            return edm
        return None

    @classmethod
    def _extract_date_display(cls, record: dict[str, object]) -> str | None:
        """Pick a human-readable date, not an ingestion epoch."""

        for key in ("year", "dctermsIssued", "dcDate", "dcDateCreated"):
            value = cls._first_text(record.get(key), default=None)
            if value:
                return value
        return None

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
