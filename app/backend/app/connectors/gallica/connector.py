"""Gallica connector implementation."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import defusedxml.ElementTree as SafeET

from app.config.settings import settings
from app.connectors.base import BaseConnector, FixtureConnectorMixin
from app.connectors.gallica.fixtures import FIXTURE_GALLICA_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.error_sanitizer import sanitize_error_message
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id

logger = logging.getLogger(__name__)


class GallicaConnector(FixtureConnectorMixin, BaseConnector):
    """Gallica/BnF connector with live SRU mode and deterministic fixture fallback."""

    name = "gallica"
    label = "Gallica / BnF"
    source_type = "institution"

    _DEFAULT_INSTITUTION = "Bibliothèque nationale de France"
    _SRW_RECORD_TAG = "{http://www.loc.gov/zing/srw/}record"
    _DC_NAMESPACES = (
        "http://purl.org/dc/elements/1.1/",
        "http://purl.org/dc/terms/",
    )
    _DC_LOCAL_NAMES = {"title", "creator", "date", "identifier", "type"}

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        start = time.perf_counter()

        if settings.gallica_use_fixtures:
            return self._fixture_search_response(query, page, page_size, start, partial=[])

        try:
            records = await self._fetch_search_records(query=query, page=page, page_size=page_size)
            items = [self._map_record(record, index) for index, record in enumerate(records)]
        except Exception as exc:
            logger.warning("Gallica live search failed, using fixtures: %s", exc)
            partial = [PartialFailure(
                source=self.name, status="degraded",
                error=f"live_gallica_unavailable: {sanitize_error_message(exc)}",
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
        records = self._search_fixtures(query, FIXTURE_GALLICA_RECORDS)
        items = [
            self._map_fixture_record(
                r, i,
                default_institution=self._DEFAULT_INSTITUTION,
                manifest_url_override=self._manifest_from_ark(str(r["source_item_id"])),
            )
            for i, r in enumerate(records)
        ]
        return self._build_search_response(
            query=query, page=page, page_size=page_size,
            items=items, partial_failures=partial,
            needs_local_pagination=True, start_time=start,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        if not settings.gallica_use_fixtures:
            try:
                records = await self._fetch_search_records(
                    query=f'ark all "{source_item_id}"',
                    page=1, page_size=1, raw_query=True,
                )
                if records:
                    return self._map_record(records[0], 0)
            except Exception as exc:
                logger.warning("Gallica live get_item failed for %s: %s", source_item_id, exc)

        return self._get_fixture_item(
            source_item_id, FIXTURE_GALLICA_RECORDS,
            default_institution=self._DEFAULT_INSTITUTION,
            manifest_url_override=self._manifest_from_ark(source_item_id),
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

        ark = self._extract_ark(source)
        return self._manifest_from_ark(ark) if ark else None

    async def healthcheck(self) -> dict[str, str]:
        if settings.gallica_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}
        try:
            params_query = quote_plus('dc.title all "test"')
            url = (
                f"{settings.gallica_sru_base_url}?version=1.2&operation=searchRetrieve"
                f"&query={params_query}&maximumRecords=1"
            )
            async with build_async_client() as client:
                response = await client.get(url)
                if response.status_code >= 400:
                    return {"status": "error", "mode": "live"}
            return {"status": "ok", "mode": "live"}
        except Exception:
            return {"status": "error", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    # -- SRU-specific internals --

    async def _fetch_search_records(
        self, query: str, page: int, page_size: int, raw_query: bool = False,
    ) -> list[ET.Element]:
        sru_query = query if raw_query else f'dc.title all "{query}"'
        start_record = ((page - 1) * page_size) + 1
        encoded_query = quote_plus(sru_query)

        url = (
            f"{settings.gallica_sru_base_url}?version=1.2&operation=searchRetrieve"
            f"&query={encoded_query}&startRecord={start_record}&maximumRecords={page_size}"
        )

        async with build_async_client() as client:
            response = await client.get(url)
            response.raise_for_status()

        root = SafeET.fromstring(response.text)
        records = list(root.iter(self._SRW_RECORD_TAG))
        if records:
            return records
        # Fallback for non-namespaced SRU responses: match exactly on tag == "record"
        # (not *record or dcrecord).
        return [node for node in root.iter() if node.tag == "record"]

    def _map_record(self, record: ET.Element, index: int) -> NormalizedItem:
        dc = self._extract_dc_values(record)
        identifiers = dc.get("identifier", [])

        source_item_id = self._extract_ark(identifiers)
        if not source_item_id:
            source_item_id = f"gallica-record-{index}"

        title = self._first(dc.get("title", []), default="Document Gallica")
        creators = dc.get("creator", [])
        # Prefer the first identifier that looks like an HTTP(S) URL, otherwise
        # any identifier; fall back to None. A raw ARK string is not a URL and
        # shouldn't be used as record_url.
        record_url = self._first_url(identifiers) or self._first(identifiers, default=None)
        if record_url and not record_url.startswith(("http://", "https://")):
            record_url = None
        manifest_url = (
            self._manifest_from_ark(source_item_id) if source_item_id.startswith("ark:/") else None
        )

        warnings: list[str] = []
        if not creators:
            warnings.append("missing_creators")
        if record_url is None:
            warnings.append("missing_record_url")

        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=title or "",
            creators=creators,
            date_display=self._first(dc.get("date", []), default=None),
            object_type=self._map_object_type(self._first(dc.get("type", []), default="other") or "other"),
            institution=self._DEFAULT_INSTITUTION,
            thumbnail_url=None,
            record_url=record_url,
            manifest_url=manifest_url,
            has_iiif_manifest=manifest_url is not None,
            has_images=True,
            has_ocr=False,
            availability="public",
            relevance_score=max(0.0, 1.0 - (index * 0.01)),
            normalization_warnings=warnings,
        )

    def _extract_dc_values(self, record: ET.Element) -> dict[str, list[str]]:
        values: dict[str, list[str]] = {}
        seen: dict[str, set[str]] = {}
        for node in record.iter():
            if not node.tag.startswith("{") or not node.text:
                continue
            namespace, _, local_name = node.tag[1:].partition("}")
            if namespace not in self._DC_NAMESPACES:
                continue
            if local_name not in self._DC_LOCAL_NAMES:
                continue
            text = node.text.strip()
            if not text:
                continue
            bucket = values.setdefault(local_name, [])
            seen_bucket = seen.setdefault(local_name, set())
            if text in seen_bucket:
                continue
            seen_bucket.add(text)
            bucket.append(text)
        return values

    def _extract_ark(self, identifiers: list[str] | str) -> str | None:
        values = [identifiers] if isinstance(identifiers, str) else identifiers
        for value in values:
            if "ark:/" not in value:
                continue
            ark = value[value.index("ark:/") :]
            return ark.split("?")[0].rstrip("/")
        return None

    def _manifest_from_ark(self, ark: str) -> str:
        return f"https://gallica.bnf.fr/iiif/{ark}/manifest.json"

    def _map_object_type(self, raw_type: str) -> str:
        lowered = raw_type.lower()
        if "manus" in lowered:
            return "manuscript"
        if "book" in lowered or "livre" in lowered:
            return "book"
        if "map" in lowered or "carte" in lowered:
            return "map"
        if "image" in lowered or "estampe" in lowered:
            return "image"
        if "journal" in lowered or "newspaper" in lowered:
            return "newspaper"
        return "other"

    @staticmethod
    def _first(values: list[str], default: str | None) -> str | None:
        return values[0] if values else default

    @staticmethod
    def _first_url(values: list[str]) -> str | None:
        for value in values:
            if value.startswith(("http://", "https://")):
                return value
        return None
