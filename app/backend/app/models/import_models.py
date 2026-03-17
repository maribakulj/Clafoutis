"""Models for import-by-URL endpoint."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.normalized_item import NormalizedItem


class ImportRequest(BaseModel):
    """Input payload for item import using a URL."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)


class ImportResponse(BaseModel):
    """Result of import URL analysis and manifest resolution."""

    detected_source: str | None = None
    record_url: str | None = None
    manifest_url: str | None = None
    item: NormalizedItem | None = None
