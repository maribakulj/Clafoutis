"""Models describing source capabilities and source listing responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProbeStatus = Literal["supported", "not_supported", "timeout", "failed", "skipped"]


class SourceCapabilities(BaseModel):
    """Capabilities declared by a connector."""

    search: bool = True
    get_item: bool = True
    resolve_manifest: bool = True


class RuntimeCapabilities(BaseModel):
    """Runtime capability matrix used by probing and capability merging."""

    free_text_search: bool
    structured_search: bool
    pagination: bool
    facets: bool
    direct_manifest_resolution: bool
    thumbnails: bool
    ocr_signal: bool
    image_availability: bool
    runtime_detection: bool
    protocol_family: str


class RuntimeProbeSnapshot(BaseModel):
    """Normalized payload describing declared, detected and effective capabilities."""

    declared_capabilities: RuntimeCapabilities
    detected_capabilities: RuntimeCapabilities | None = None
    effective_capabilities: RuntimeCapabilities
    probe_status: ProbeStatus
    probe_message: str | None = None
    probe_timestamp: datetime | None = None
    probe_source: str | None = None
    supports_runtime_detection: bool
    capability_warnings: list[str] = Field(default_factory=list)


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
