"""Error payload model for consistent API error responses."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Structured error payload returned by exception handlers."""

    error: str
    details: str | None = None
