"""Search endpoint."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_search_orchestrator
from app.models.search_models import SearchRequest, SearchResponse
from app.services.search_orchestrator import SearchOrchestrator

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_items(
    payload: SearchRequest,
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator),
) -> SearchResponse:
    """Run federated search and return normalized results."""

    return await orchestrator.search(payload)
