"""Service for item retrieval by global identifier."""

from app.connectors.registry import ConnectorRegistry
from app.models.normalized_item import NormalizedItem
from app.utils.errors import BadRequestError, NotFoundError
from app.utils.ids import split_global_id


class ItemService:
    """Resolve item details using global id policy source:source_item_id."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    async def get_item(self, global_id: str) -> NormalizedItem:
        """Fetch normalized item from connector using global id."""

        try:
            source, source_item_id = split_global_id(global_id)
        except ValueError:
            raise BadRequestError("Invalid id format, expected source:source_item_id")
        if not self._registry.has(source):
            raise NotFoundError(f"Unknown source '{source}'")
        item = await self._registry.get(source).get_item(source_item_id)
        if item is None:
            raise NotFoundError(f"Item '{global_id}' not found")
        return item
