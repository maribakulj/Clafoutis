"""Models for search requests and responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.normalized_item import NormalizedItem


class SearchFilters(BaseModel):
    """Well-known filters applied post-aggregation across sources.

    Filter fields are all optional: ``None`` means "no constraint".
    Connectors may receive the same filter payload for native filtering,
    but the orchestrator is the source of truth for post-filtering.
    """

    model_config = ConfigDict(extra="forbid")

    has_iiif_manifest: bool | None = None
    object_type: list[str] | None = None
    languages: list[str] | None = None


class SearchRequest(BaseModel):
    """Input payload for federated search."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    sources: list[str] | None = None
    filters: SearchFilters = Field(default_factory=SearchFilters)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)


class PartialFailure(BaseModel):
    """Per-source failure report. Only present when a source had issues."""

    source: str
    status: Literal["degraded", "error"]
    error: str | None = None


class SearchResponse(BaseModel):
    """Unified search response returned by backend APIs."""

    query: str
    page: int
    page_size: int
    total_estimated: int
    has_next_page: bool = False
    results: list[NormalizedItem]
    sources_used: list[str]
    partial_failures: list[PartialFailure] = Field(default_factory=list)
    duration_ms: int
