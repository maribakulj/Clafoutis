"""Top-level API router."""

from fastapi import APIRouter

from app.api import health, import_, items, manifest, search, sources
from app.api import open as open_api

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(sources.router)
api_router.include_router(search.router)
api_router.include_router(items.router)
api_router.include_router(manifest.router)
api_router.include_router(import_.router)
api_router.include_router(open_api.router)
