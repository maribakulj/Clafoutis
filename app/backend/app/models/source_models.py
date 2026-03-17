"""Models describing source capabilities and source listing responses."""

from pydantic import BaseModel, Field


class SourceCapabilities(BaseModel):
    """Capabilities declared by a connector."""

    search: bool = True
    get_item: bool = True
    resolve_manifest: bool = True


class SourceDescriptor(BaseModel):
    """Source metadata exposed through /api/sources."""

    name: str
    label: str
    source_type: str
    capabilities: SourceCapabilities
    healthy: bool
    notes: str | None = None


class SourcesResponse(BaseModel):
    """Response payload for source listing endpoint."""

    sources: list[SourceDescriptor] = Field(default_factory=list)
