"""Federated search orchestration over registered connectors."""

from __future__ import annotations

import asyncio
import re
import time
import unicodedata

from app.config.settings import settings
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import (
    PartialFailure,
    SearchFilters,
    SearchRequest,
    SearchResponse,
)
from app.utils.error_sanitizer import sanitize_error_message


class SearchOrchestrator:
    """Coordinate multi-source search with partial failure tolerance."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Run federated search across selected connectors and merge results.

        Pagination policy: each connector is already asked for ``page`` and
        ``page_size`` and returns its own page of results. The orchestrator
        does not re-paginate the merged stream (which would silently drop
        cross-source results); it simply interleaves results ordered by
        relevance and reports ``has_next_page`` when *any* source suggests
        more results exist.

        Ranking: each item gets a small completeness bonus on top of its
        source-native relevance score (presence of a manifest, thumbnail,
        creators, date). Items sharing a manifest URL or normalized
        (title, date) are deduplicated weakly — the highest-scoring
        duplicate wins; we never collapse distinct sources aggressively
        per specs §16.2.

        Robustness: each per-source task is individually wrapped in a
        ``asyncio.wait_for`` using ``request_timeout_seconds`` so a single
        hanging source cannot stall the whole federated response.
        """

        selected = request.sources or self._registry.list_names()
        tasks = [self._search_one_with_timeout(source, request) for source in selected]
        start = time.perf_counter()
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        duration_ms = int((time.perf_counter() - start) * 1000)

        merged_results: list[NormalizedItem] = []
        partial_failures: list[PartialFailure] = []
        sources_used: list[str] = []
        total_estimated = 0
        any_source_has_next = False

        for source_name, outcome in zip(selected, gathered, strict=True):
            if isinstance(outcome, asyncio.TimeoutError):
                partial_failures.append(
                    PartialFailure(source=source_name, status="error", error="timeout")
                )
                continue
            if not isinstance(outcome, SearchResponse):
                partial_failures.append(
                    PartialFailure(
                        source=source_name,
                        status="error",
                        error=sanitize_error_message(outcome),
                    )
                )
                continue
            sources_used.append(source_name)
            merged_results.extend(outcome.results)
            total_estimated += outcome.total_estimated
            if outcome.has_next_page or (
                outcome.total_estimated > request.page * request.page_size
            ):
                any_source_has_next = True
            # PartialFailure.status is Literal["degraded", "error"] so every
            # entry from a connector is a real failure that must be forwarded.
            partial_failures.extend(outcome.partial_failures)

        merged_results = [
            item for item in merged_results if _matches_filters(item, request.filters)
        ]
        merged_results = _rerank(merged_results)
        merged_results = _deduplicate(merged_results)

        return SearchResponse(
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            total_estimated=total_estimated,
            has_next_page=any_source_has_next,
            results=merged_results,
            sources_used=sources_used,
            partial_failures=partial_failures,
            duration_ms=duration_ms,
        )

    async def _search_one_with_timeout(
        self, source: str, request: SearchRequest
    ) -> SearchResponse:
        return await asyncio.wait_for(
            self._search_one(source, request),
            timeout=settings.request_timeout_seconds,
        )

    async def _search_one(self, source: str, request: SearchRequest) -> SearchResponse:
        if not self._registry.has(source):
            raise ValueError(f"Unknown source '{source}'")
        connector = self._registry.get(source)
        # Connectors receive the filter payload as a dict for future native
        # filtering. The orchestrator remains the source of truth (post-filter).
        return await connector.search(
            query=request.query,
            filters=request.filters.model_dump(exclude_none=True),
            page=request.page,
            page_size=request.page_size,
        )


def _matches_filters(item: NormalizedItem, filters: SearchFilters) -> bool:
    """Return True when ``item`` satisfies every non-None filter constraint."""

    if filters.has_iiif_manifest is True and not item.has_iiif_manifest:
        return False
    if filters.has_iiif_manifest is False and item.has_iiif_manifest:
        return False
    if filters.object_type and item.object_type not in filters.object_type:
        return False
    if filters.languages:
        if not item.languages:
            return False
        if not any(lang in filters.languages for lang in item.languages):
            return False
    return True


def _completeness_bonus(item: NormalizedItem) -> float:
    """Small additive bonus rewarding richer records (keeps score in [0,1])."""

    bonus = 0.0
    if item.has_iiif_manifest:
        bonus += 0.05
    if item.thumbnail_url:
        bonus += 0.02
    if item.creators:
        bonus += 0.01
    if item.date_display:
        bonus += 0.01
    if item.institution:
        bonus += 0.005
    return bonus


def _rerank(items: list[NormalizedItem]) -> list[NormalizedItem]:
    """Sort items by adjusted score (native relevance + completeness bonus)."""

    return sorted(
        items,
        key=lambda item: item.relevance_score + _completeness_bonus(item),
        reverse=True,
    )


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_title(value: str) -> str:
    """Normalize a title for weak duplicate detection.

    Strips accents, lowercases, collapses whitespace and punctuation. The
    purpose is comparison only; never store or display the normalized form.
    """

    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = without_marks.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def _deduplicate(items: list[NormalizedItem]) -> list[NormalizedItem]:
    """Collapse obvious duplicates while preserving source diversity.

    Policy:
    - Two items sharing a non-empty ``manifest_url`` are considered the
      same object — keep the first (highest-ranked).
    - Two items whose normalized ``(title, date_display)`` tuple matches
      are considered a soft duplicate — keep the first.

    Items are assumed to be pre-sorted by rank so the survivor is the
    best-ranked one. Nothing is fused cross-source: a weak match still
    yields a single item rather than synthesizing a merged record.
    """

    seen_manifests: set[str] = set()
    seen_soft_keys: set[tuple[str, str | None]] = set()
    unique: list[NormalizedItem] = []

    for item in items:
        if item.manifest_url:
            if item.manifest_url in seen_manifests:
                continue
            seen_manifests.add(item.manifest_url)

        normalized_title = _normalize_title(item.title) if item.title else ""
        soft_key = (normalized_title, item.date_display)
        if normalized_title and soft_key in seen_soft_keys:
            continue
        if normalized_title:
            seen_soft_keys.add(soft_key)

        unique.append(item)

    return unique
