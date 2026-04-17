"""Custom Starlette middleware for security headers and body size limits."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Content-Security-Policy tuned for a Mirador-hosting SPA: Mirador performs
# cross-origin fetches to IIIF services and renders inline styles. Keep it
# explicit rather than relying on "unsafe-*" blanket allowances.
_DEFAULT_CSP = (
    "default-src 'self'; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' https:; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self' data: https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'"
)

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": _DEFAULT_CSP,
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to every response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared Content-Length exceeds ``max_bytes``.

    Only declared length is enforced; streaming clients that lie about their
    size are limited instead by the ASGI server / reverse proxy. The goal is
    a cheap early rejection against naive DoS payloads.
    """

    def __init__(self, app, *, max_bytes: int) -> None:
        super().__init__(app)
        if max_bytes <= 0:
            raise ValueError("max_bytes must be > 0")
        self._max_bytes = max_bytes

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"error": "bad_request", "details": "invalid content-length"},
                )
            if length > self._max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"error": "payload_too_large", "details": None},
                )
        return await call_next(request)
