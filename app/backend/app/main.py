"""FastAPI application entrypoint for backend lot 1."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config.settings import settings
from app.models.error_models import ErrorResponse
from app.utils.errors import AppError, BadRequestError, NotFoundError


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    application = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)

    frontend_dist = Path(settings.frontend_dist_dir)
    frontend_index = frontend_dist / "index.html"

    frontend_assets = frontend_dist / "assets"

    if settings.serve_frontend and frontend_dist.exists() and frontend_index.exists() and frontend_assets.exists():
        application.mount(
            "/assets",
            StaticFiles(directory=frontend_assets),
            name="frontend-assets",
        )

        @application.get("/", include_in_schema=False)
        async def root_index() -> FileResponse:
            """Serve frontend SPA index page when bundled assets are available."""

            return FileResponse(frontend_index)

        @application.get("/{full_path:path}", include_in_schema=False)
        async def frontend_fallback(full_path: str) -> FileResponse:
            """Serve SPA fallback for non-API routes in single-container deployment."""

            if full_path.startswith("api/"):
                payload = ErrorResponse(error="not_found", details="endpoint not found").model_dump()
                return JSONResponse(status_code=404, content=payload)
            return FileResponse(frontend_index)

    @application.exception_handler(BadRequestError)
    async def handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
        payload = ErrorResponse(error="bad_request", details=str(exc)).model_dump()
        return JSONResponse(status_code=400, content=payload)

    @application.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        payload = ErrorResponse(error="not_found", details=str(exc)).model_dump()
        return JSONResponse(status_code=404, content=payload)

    @application.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        payload = ErrorResponse(error="application_error", details=str(exc)).model_dump()
        return JSONResponse(status_code=500, content=payload)

    return application


app = create_app()
