"""Gallica connector implementation."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from app.config.settings import settings
from app.connectors.base import BaseConnector, FixtureConnectorMixin
from app.connectors.gallica.fixtures import FIXTURE_GALLICA_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id

try:
    import defusedxml.ElementTree as SafeET
except ImportError:  # pragma: no cover
    SafeET = ET  # type: ignore[misc]

logger = logging.getLogger(__name__)


class GallicaConnector(FixtureConnectorMixin, BaseConnector):
    """Gallica/BnF connector with live SRU mode and deterministic fixture fallback."""

    name = "gallica"
    label = "Gallica / BnF"
    source_type = "institution"

    _DEFAULT_INSTITUTION = "Bibliothèque nationale de France"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        start = time.perf_counter()
        needs_local_pagination = False
        try:
            records = await self._fetch_search_records(query=query, page=page, page_size=page_size)
            items = [self._map_record(record, index) for index, record in enumerate(records)]
            partial: list[PartialFailure] = []
        except Exception as exc:
            needs_local_pagination = True
            records = self._search_fixtures(query, FIXTURE_GALLICA_RECORDS)
            items = [
                self._map_fixture_record(
                    r, i,
                    default_institution=self._DEFAULT_INSTITUTION,
                    manifest_url_override=self._manifest_from_ark(str(r["source_item_id"])),
                )
                for i, r in enumerate(records)
            ]
            partial = [PartialFailure(
                source=self.name, status="degraded",
                error=f"live_gallica_unavailable: {exc}",
            )]

        return self._build_search_response(
            query=query, page=page, page_size=page_size,
            items=items, partial_failures=partial,
            needs_local_pagination=needs_local_pagination, start_time=start,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
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

        params_query = quote_plus('dc.title all "dante"')
        url = (
            f"{settings.gallica_sru_base_url}?version=1.2&operation=searchRetrieve"
            f"&query={params_query}&maximumRecords=1"
        )
        async with build_async_client() as client:
            response = await client.get(url)
            if response.status_code >= 400:
                return {"status": "error", "mode": "live"}
        return {"status": "ok", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    # -- SRU-specific internals --

    async def _fetch_search_records(
        self, query: str, page: int, page_size: int, raw_query: bool = False,
    ) -> list[ET.Element]:
        if settings.gallica_use_fixtures:
            raise RuntimeError("fixtures mode enabled")

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
        return [record for record in root.iter() if record.tag.endswith("record")]

    def _map_record(self, record: ET.Element, index: int) -> NormalizedItem:
        dc = self._extract_dc_values(record)

        source_item_id = self._extract_ark(dc.get("identifier", []))
        if not source_item_id:
            source_item_id = f"gallica-record-{index}"

        title = self._first(dc.get("title", []), default="Document Gallica")
        creators = dc.get("creator", [])
        record_url = self._first(dc.get("identifier", []), default=None)
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
        for node in record.iter():
            if not node.tag.startswith("{"):
                continue
            local_name = node.tag.split("}", maxsplit=1)[1]
            if local_name in {"title", "creator", "date", "identifier", "type"} and node.text:
                values.setdefault(local_name, []).append(node.text.strip())
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
