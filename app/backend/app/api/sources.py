"""Source listing endpoint."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_source_service
from app.models.source_models import SourcesResponse
from app.services.source_service import SourceService

router = APIRouter(tags=["sources"])


@router.get("/sources", response_model=SourcesResponse)
async def list_sources(service: SourceService = Depends(get_source_service)) -> SourcesResponse:
    """List registered sources and capabilities."""

    return await service.list_sources()
