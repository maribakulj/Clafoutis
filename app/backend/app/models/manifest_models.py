"""Models for manifest resolution operations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ResolveManifestRequest(BaseModel):
    """Input payload for manifest resolution."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    source_item_id: str = Field(min_length=1)
    record_url: str | None = None


class ResolveManifestResponse(BaseModel):
    """Output payload for manifest resolution."""

    manifest_url: str | None = None
    status: Literal["resolved", "not_found"]
    method: str | None = None
