"""Generic connector resolving IIIF manifests from arbitrary URLs."""

from __future__ import annotations

from urllib.parse import urlparse

from app.connectors.base import BaseConnector
from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchResponse
from app.models.source_models import SourceCapabilities


class ManifestByUrlConnector(BaseConnector):
    """Connector dedicated to URL import and generic manifest detection heuristics."""

    name = "manifest_by_url"
    label = "Manifest by URL"
    source_type = "generic"

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Return empty search results because this connector is import-only."""

        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total_estimated=0,
            results=[],
            sources_used=[self.name],
            partial_failures=[],
            duration_ms=1,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        """Return no item because this connector does not expose source IDs."""

        return None

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve manifest URL by direct detection or lightweight notice heuristics."""

        candidate_url = record_url or (item.record_url if item else None)
        if not candidate_url:
            return None

        # Heuristic 1: direct manifest URL patterns
        if self._looks_like_manifest_url(candidate_url):
            return candidate_url

        # Heuristic 2: common notice -> manifest patterns
        generated_candidates = self._notice_to_manifest_candidates(candidate_url)
        for candidate in generated_candidates:
            if self._looks_like_manifest_url(candidate):
                return candidate

        return None

    async def healthcheck(self) -> dict[str, str]:
        """Return healthy status for the local heuristic connector."""

        return {"status": "ok"}

    async def capabilities(self) -> SourceCapabilities:
        """Declare capabilities for this connector."""

        return SourceCapabilities(search=False, get_item=False, resolve_manifest=True)

    def _looks_like_manifest_url(self, url: str) -> bool:
        parsed = urlparse(url)
        lowered_path = parsed.path.lower()
        lowered_query = parsed.query.lower()
        return (
            "manifest" in lowered_path
            or lowered_path.endswith("manifest.json")
            or lowered_query.startswith("manifest=")
            or "iiif_manifest" in lowered_query
        )

    def _notice_to_manifest_candidates(self, url: str) -> list[str]:
        parsed = urlparse(url)
        clean_path = parsed.path.rstrip("/")

        suffixes = [
            "/manifest",
            "/manifest.json",
            "/iiif/manifest",
            "/iiif/manifest.json",
        ]

        candidates: list[str] = []
        for suffix in suffixes:
            candidate = parsed._replace(path=f"{clean_path}{suffix}", query="").geturl()
            candidates.append(candidate)

        return candidates
