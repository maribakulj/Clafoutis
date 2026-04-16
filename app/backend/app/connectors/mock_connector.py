"""Mock connector used by backend lot 1 to provide stable demo data."""

from app.connectors.base import BaseConnector
from app.models.normalized_item import NormalizedItem
from app.models.search_models import SearchResponse
from app.models.source_models import SourceCapabilities
from app.utils.ids import make_global_id


class MockConnector(BaseConnector):
    """Simple in-memory connector implementing BaseConnector contract."""

    name = "mock"
    label = "Mock Heritage Source"
    source_type = "mock"

    def __init__(self) -> None:
        self._items = {
            "ms-1": NormalizedItem(
                id=make_global_id("mock", "ms-1"),
                source="mock",
                source_label=self.label,
                source_item_id="ms-1",
                title="Book of Hours (Mock)",
                creators=["Unknown"],
                institution="Mock Institution",
                object_type="manuscript",
                record_url="https://mock.example.org/items/ms-1",
                manifest_url="https://mock.example.org/iiif/ms-1/manifest",
                has_iiif_manifest=True,
                has_images=True,
                has_ocr=False,
                availability="public",
                relevance_score=0.9,
            ),
            "ms-2": NormalizedItem(
                id=make_global_id("mock", "ms-2"),
                source="mock",
                source_label=self.label,
                source_item_id="ms-2",
                title="Dante Manuscript (Mock)",
                creators=["Anonymous"],
                institution="Mock Institution",
                object_type="manuscript",
                record_url="https://mock.example.org/items/ms-2",
                manifest_url=None,
                has_iiif_manifest=False,
                has_images=True,
                has_ocr=True,
                availability="public",
                relevance_score=0.8,
            ),
        }

    async def search(
        self,
        query: str,
        filters: dict[str, object],
        page: int,
        page_size: int,
    ) -> SearchResponse:
        """Return normalized in-memory results filtered by query substring."""

        lowered = query.lower().strip()
        filtered = [item for item in self._items.values() if lowered in item.title.lower()]
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]
        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total_estimated=len(filtered),
            results=page_items,
            sources_used=[self.name],
            partial_failures=[],
            duration_ms=1,
        )

    async def get_item(self, source_item_id: str) -> NormalizedItem | None:
        """Return normalized item when available."""

        return self._items.get(source_item_id)

    async def resolve_manifest(
        self,
        item: NormalizedItem | None = None,
        record_url: str | None = None,
    ) -> str | None:
        """Resolve manifest URL from provided item or known record URL."""

        if item is not None and item.manifest_url:
            return item.manifest_url

        if record_url:
            for candidate in self._items.values():
                if candidate.record_url == record_url:
                    return candidate.manifest_url
        return None

    async def healthcheck(self) -> dict[str, str]:
        """Return static healthy status for demonstration connector."""

        return {"status": "ok"}

    async def capabilities(self) -> SourceCapabilities:
        """Return static capabilities for the mock connector."""

        return SourceCapabilities(search=True, get_item=True, resolve_manifest=True)
