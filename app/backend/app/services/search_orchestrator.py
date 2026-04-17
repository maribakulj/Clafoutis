"""Federated search orchestration over registered connectors."""

from __future__ import annotations

import asyncio
import time

from app.config.settings import settings
from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.models.search_models import PartialFailure, SearchRequest, SearchResponse
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
            # Only propagate actual failures, not status="ok" entries
            for pf in outcome.partial_failures:
                if pf.status != "ok":
                    partial_failures.append(pf)

        merged_results.sort(key=lambda item: item.relevance_score, reverse=True)

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
        return await connector.search(
            query=request.query,
            filters=request.filters,
            page=request.page,
            page_size=request.page_size,
        )
