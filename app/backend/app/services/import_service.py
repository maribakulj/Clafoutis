"""Service for URL import and initial source detection."""

from app.connectors.registry import ConnectorRegistry
from app.models.import_models import ImportResponse
from app.utils.url_validation import validate_http_url


class ImportService:
    """Handle import flow from URL to normalized item and manifest."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def import_url(self, url: str) -> ImportResponse:
        """Validate URL then resolve manifest through source and generic connectors.

        Resolution order:
        1. Source-specific connectors (e.g. mock) try exact record URL mapping.
        2. `manifest_by_url` connector applies generic URL heuristics:
           - direct manifest pattern detection;
           - notice -> manifest candidate generation.
        """

        safe_url = validate_http_url(url)

        source_connectors = [
            connector
            for connector in self._registry.list_connectors()
            if connector.name != "manifest_by_url"
        ]
        generic_connectors = [
            connector
            for connector in self._registry.list_connectors()
            if connector.name == "manifest_by_url"
        ]

        for connector in [*source_connectors, *generic_connectors]:
            matched_item = None
            if connector.name == "mock":
                # Lot 4 keeps source-specific matching minimal for mock demo data.
                for candidate_id in ("ms-1", "ms-2"):
                    candidate = await connector.get_item(candidate_id)
                    if candidate is not None and candidate.record_url == safe_url:
                        matched_item = candidate
                        break

            manifest = await connector.resolve_manifest(item=matched_item, record_url=safe_url)
            if manifest:
                return ImportResponse(
                    detected_source=connector.name,
                    record_url=safe_url,
                    manifest_url=manifest,
                    item=matched_item,
                )

        return ImportResponse(
            detected_source=None,
            record_url=safe_url,
            manifest_url=None,
            item=None,
        )
