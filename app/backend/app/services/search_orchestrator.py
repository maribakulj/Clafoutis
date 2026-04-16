"""Federated search orchestration over registered connectors."""

from __future__ import annotations

import asyncio
import time

from app.connectors.registry import ConnectorRegistry
from app.models.search_models import PartialFailure, SearchRequest, SearchResponse


class SearchOrchestrator:
    """Coordinate multi-source search with partial failure tolerance."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Run federated search across selected connectors and merge results."""

        selected = request.sources or self._registry.list_names()
        tasks = [self._search_one(source, request) for source in selected]
        start = time.perf_counter()
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        duration_ms = int((time.perf_counter() - start) * 1000)

        merged_results = []
        partial_failures: list[PartialFailure] = []
        sources_used: list[str] = []

        for source_name, outcome in zip(selected, gathered, strict=True):
            if isinstance(outcome, Exception):
                partial_failures.append(
                    PartialFailure(source=source_name, status="error", error=str(outcome))
                )
                continue
            sources_used.append(source_name)
            merged_results.extend(outcome.results)
            partial_failures.extend(outcome.partial_failures)

        merged_results.sort(key=lambda item: item.relevance_score, reverse=True)

        total = len(merged_results)
        start_index = (request.page - 1) * request.page_size
        paginated = merged_results[start_index : start_index + request.page_size]

        return SearchResponse(
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            total_estimated=total,
            results=paginated,
            sources_used=sources_used,
            partial_failures=partial_failures,
            duration_ms=duration_ms,
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
