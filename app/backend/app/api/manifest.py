"""Manifest resolution endpoint."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_manifest_resolver
from app.models.manifest_models import ResolveManifestRequest, ResolveManifestResponse
from app.services.manifest_resolver import ManifestResolver

router = APIRouter(tags=["manifest"])


@router.post("/resolve-manifest", response_model=ResolveManifestResponse)
async def resolve_manifest(
    payload: ResolveManifestRequest,
    resolver: ManifestResolver = Depends(get_manifest_resolver),
) -> ResolveManifestResponse:
    """Resolve manifest URL for a source item."""

    return await resolver.resolve(payload)
