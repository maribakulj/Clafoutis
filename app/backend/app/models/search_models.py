"""Models for search requests and responses."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.normalized_item import NormalizedItem


class SearchRequest(BaseModel):
    """Input payload for federated search."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    sources: list[str] | None = None
    filters: dict[str, object] = Field(default_factory=dict)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)


class PartialFailure(BaseModel):
    """Per-source failure report for partial success responses."""

    source: str
    status: str
    error: str | None = None


class SearchResponse(BaseModel):
    """Unified search response returned by backend APIs."""

    query: str
    page: int
    page_size: int
    total_estimated: int
    results: list[NormalizedItem]
    sources_used: list[str]
    partial_failures: list[PartialFailure] = Field(default_factory=list)
    duration_ms: int
