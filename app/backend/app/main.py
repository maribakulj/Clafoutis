"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config.settings import settings
from app.models.error_models import ErrorResponse
from app.utils.error_sanitizer import sanitize_error_message
from app.utils.errors import AppError, BadRequestError, NotFoundError
from app.utils.http_client import reset_shared_client
from app.utils.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def _mount_frontend(application: FastAPI) -> None:
    """Mount built frontend SPA assets and catch-all route."""

    frontend_dist = Path(settings.frontend_dist_dir)
    index_file = frontend_dist / "index.html"

    if not index_file.exists():
        return

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        application.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="frontend-assets",
        )

    @application.get("/", include_in_schema=False)
    async def serve_frontend_index() -> FileResponse:
        return FileResponse(index_file)

    @application.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        candidate = (frontend_dist / full_path).resolve()
        if not str(candidate).startswith(str(frontend_dist.resolve())):
            return JSONResponse(status_code=400, content={"detail": "Invalid path"})
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage process-wide resources (shared httpx client) across app lifetime."""

    try:
        yield
    finally:
        await reset_shared_client()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=_lifespan,
    )

    # Middleware ordering: outermost first. Security headers wrap every
    # response; CORS handles preflights before the app sees them; the body
    # size guard rejects oversized payloads cheaply before routing.
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    application.add_middleware(
        BodySizeLimitMiddleware, max_bytes=settings.max_request_body_bytes
    )
    application.include_router(api_router)

    @application.exception_handler(BadRequestError)
    async def handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
        payload = ErrorResponse(error="bad_request", details=sanitize_error_message(exc)).model_dump()
        return JSONResponse(status_code=400, content=payload)

    @application.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        payload = ErrorResponse(error="not_found", details=sanitize_error_message(exc)).model_dump()
        return JSONResponse(status_code=404, content=payload)

    @application.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        payload = ErrorResponse(
            error="application_error", details=sanitize_error_message(exc)
        ).model_dump()
        return JSONResponse(status_code=500, content=payload)

    if settings.serve_frontend:
        _mount_frontend(application)

    return application


app = create_app()
