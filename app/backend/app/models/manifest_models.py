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


class OpenInMiradorRequest(BaseModel):
    """Input payload for ``/api/open`` — open manifests in a Mirador workspace."""

    model_config = ConfigDict(extra="forbid")

    manifest_urls: list[str] = Field(min_length=1, max_length=16)
    workspace: str = "default"


class MiradorWorkspaceState(BaseModel):
    """Compact Mirador-compatible workspace state returned by ``/api/open``."""

    windows: list[dict[str, str]]
    catalog: list[dict[str, str]]
    workspace: dict[str, object]


class OpenInMiradorResponse(BaseModel):
    """Output payload for ``/api/open``."""

    manifest_urls: list[str]
    mirador_state: MiradorWorkspaceState
