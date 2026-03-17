"""Item detail endpoint."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_item_service
from app.models.normalized_item import NormalizedItem
from app.services.item_service import ItemService

router = APIRouter(tags=["items"])


@router.get("/item/{global_id}", response_model=NormalizedItem)
async def get_item(
    global_id: str,
    service: ItemService = Depends(get_item_service),
) -> NormalizedItem:
    """Return a normalized item by global identifier."""

    return await service.get_item(global_id)
