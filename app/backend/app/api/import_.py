"""Import endpoint for notice or manifest URLs."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_import_service
from app.models.import_models import ImportRequest, ImportResponse
from app.services.import_service import ImportService

router = APIRouter(tags=["import"])


@router.post("/import", response_model=ImportResponse)
async def import_item(
    payload: ImportRequest,
    service: ImportService = Depends(get_import_service),
) -> ImportResponse:
    """Import an external URL and attempt to resolve source and manifest."""

    return await service.import_url(payload.url)
