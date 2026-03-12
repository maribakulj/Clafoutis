"""Abstract connector interface for all external sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchResponse
from app.models.source_models import SourceCapabilities


class BaseConnector(ABC):
    """Common contract implemented by every source connector."""

    name: str
    label: str
    source_type: str

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Execute source search and return normalized results."""

    @abstractmethod
    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        """Get a single normalized item by source-specific identifier."""

    @abstractmethod
    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve a IIIF manifest URL from item metadata or record URL."""

    @abstractmethod
    async def healthcheck(self) -> dict[str, str]:
        """Check connector health and return a compact status report."""

    @abstractmethod
    async def capabilities(self) -> SourceCapabilities:
        """Declare static connector capabilities."""
