"""URL validation helpers for import and manifest resolution endpoints."""

from urllib.parse import urlparse

from app.utils.errors import BadRequestError


def validate_http_url(url: str) -> str:
    """Validate that URL uses HTTP(S) and contains a host."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise BadRequestError("URL scheme must be http or https")
    if not parsed.netloc:
        raise BadRequestError("URL must contain a host")
    return url
