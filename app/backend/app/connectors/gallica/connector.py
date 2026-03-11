"""Gallica connector implementation."""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from app.config.settings import settings
from app.connectors.base import BaseConnector
from app.connectors.gallica.fixtures import FIXTURE_GALLICA_RECORDS
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.http_client import build_async_client
from app.utils.ids import make_global_id


class GallicaConnector(BaseConnector):
    """Gallica/BnF connector with live SRU mode and deterministic fixture fallback."""

    name = "gallica"
    label = "Gallica / BnF"
    source_type = "institution"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Search Gallica through SRU and map records to NormalizedItem."""

        start = time.perf_counter()
        try:
            records = await self._fetch_search_records(query=query, page=page, page_size=page_size)
            items = [self._map_record(record, index) for index, record in enumerate(records)]
            partial = [PartialFailure(source=self.name, status="ok")]
        except Exception as exc:
            records = self._search_fixtures(query)
            items = [self._map_fixture_record(record, index) for index, record in enumerate(records)]
            partial = [
                PartialFailure(
                    source=self.name,
                    status="degraded",
                    error=f"live_gallica_unavailable: {exc}",
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
        """Retrieve one Gallica item by ARK, using live mode then fixtures fallback."""

        try:
            records = await self._fetch_search_records(
                query=f'ark all "{source_item_id}"',
                page=1,
                page_size=1,
                raw_query=True,
            )
            if records:
                return self._map_record(records[0], 0)
        except Exception:
            pass

        for fixture in FIXTURE_GALLICA_RECORDS:
            if fixture["source_item_id"] == source_item_id:
                return self._map_fixture_record(fixture, 0)
        return None

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve Gallica IIIF manifest from normalized item or record URL."""

        if item and item.manifest_url:
            return item.manifest_url

        source = record_url or (item.record_url if item else None)
        if not source:
            return None

        ark = self._extract_ark(source)
        if not ark:
            return None

        return self._manifest_from_ark(ark)

    async def healthcheck(self) -> dict[str, str]:
        """Run lightweight Gallica availability check."""

        if settings.gallica_use_fixtures:
            return {"status": "ok", "mode": "fixtures"}

        params_query = quote_plus('dc.title all "dante"')
        url = (
            f"{settings.gallica_sru_base_url}?version=1.2&operation=searchRetrieve"
            f"&query={params_query}&maximumRecords=1"
        )

        async with await build_async_client() as client:
            response = await client.get(url)
            if response.status_code >= 400:
                return {"status": "error", "mode": "live"}
        return {"status": "ok", "mode": "live"}

    async def capabilities(self) -> SourceCapabilities:
        """Return Gallica connector capabilities."""

        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)

    async def _fetch_search_records(
        self,
        query: str,
        page: int,
        page_size: int,
        raw_query: bool = False,
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

        async with await build_async_client() as client:
            response = await client.get(url)
            response.raise_for_status()

        root = ET.fromstring(response.text)
        return [record for record in root.iter() if record.tag.endswith("record")]

    def _map_record(self, record: ET.Element, index: int) -> NormalizedItem:
        dc_values = self._extract_dc_values(record)

        source_item_id = self._extract_ark(dc_values.get("identifier", []))
        if not source_item_id:
            source_item_id = f"gallica-record-{index}"

        title = self._first(dc_values.get("title", []), default="Document Gallica")
        creators = dc_values.get("creator", [])
        date_display = self._first(dc_values.get("date", []), default=None)
        object_type = self._map_object_type(self._first(dc_values.get("type", []), default="other"))
        record_url = self._first(dc_values.get("identifier", []), default=None)
        manifest_url = self._manifest_from_ark(source_item_id) if source_item_id.startswith("ark:/") else None

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
            title=title,
            creators=creators,
            date_display=date_display,
            object_type=object_type,
            institution="Bibliothèque nationale de France",
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

    def _map_fixture_record(self, fixture: dict[str, object], index: int) -> NormalizedItem:
        source_item_id = str(fixture["source_item_id"])
        manifest_url = self._manifest_from_ark(source_item_id)
        return NormalizedItem(
            id=make_global_id(self.name, source_item_id),
            source=self.name,
            source_label=self.label,
            source_item_id=source_item_id,
            title=str(fixture["title"]),
            creators=[str(value) for value in fixture.get("creators", [])],
            date_display=str(fixture.get("date_display")) if fixture.get("date_display") else None,
            object_type=str(fixture.get("object_type", "other")),
            institution=str(fixture.get("institution")) if fixture.get("institution") else None,
            thumbnail_url=str(fixture.get("thumbnail_url")) if fixture.get("thumbnail_url") else None,
            record_url=str(fixture.get("record_url")) if fixture.get("record_url") else None,
            manifest_url=manifest_url,
            has_iiif_manifest=True,
            has_images=True,
            has_ocr=False,
            availability="public",
            relevance_score=max(0.0, 1.0 - (index * 0.01)),
            normalization_warnings=["fixture_mode"],
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

    def _search_fixtures(self, query: str) -> list[dict[str, object]]:
        lowered = query.lower().strip()
        return [
            record
            for record in FIXTURE_GALLICA_RECORDS
            if lowered in str(record["title"]).lower() or lowered in " ".join(record.get("creators", [])).lower()
        ]

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

    def _first(self, values: list[str], default: str | None) -> str | None:
        return values[0] if values else default
