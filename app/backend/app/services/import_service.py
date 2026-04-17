"""Service for URL import and initial source detection."""

from app.connectors.registry import ConnectorRegistry
from app.models.import_models import ImportResponse
from app.utils.url_validation import validate_http_url


class ImportService:
    """Handle import flow from URL to normalized item and manifest."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def import_url(self, url: str) -> ImportResponse:
        """Validate URL and try to resolve manifest through connectors."""

        safe_url = validate_http_url(url)
        for connector in self._registry.list_connectors():
            matched_item = await connector.find_by_record_url(safe_url)
            manifest = await connector.resolve_manifest(
                item=matched_item, record_url=safe_url
            )
            if manifest:
                return ImportResponse(
                    detected_source=connector.name,
                    record_url=safe_url,
                    manifest_url=manifest,
                    item=matched_item,
                )
        return ImportResponse(
            detected_source=None, record_url=safe_url, manifest_url=None, item=None
        )
