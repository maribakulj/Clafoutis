"""Models describing source capabilities and source listing responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProbeStatus = Literal["supported", "not_supported", "skipped", "timeout", "failed"]


class SourceCapabilities(BaseModel):
    """Connector capability declaration with legacy and normalized fields."""

    # Legacy fields kept for backward compatibility in existing connectors.
    search: bool = True
    get_item: bool = True
    resolve_manifest: bool = True

    # Normalized capability fields for runtime probing model.
    free_text_search: bool = True
    structured_search: bool = False
    pagination: bool = True
    facets: bool = False
    direct_manifest_resolution: bool = True
    thumbnails: bool = False
    ocr_signal: bool = False
    image_availability: bool = True
    runtime_detection: bool = False
    protocol_family: str = "static"

    def to_runtime_capabilities(self) -> "RuntimeCapabilities":
        """Convert declaration into normalized runtime capability structure."""

        return RuntimeCapabilities(
            free_text_search=self.free_text_search and self.search,
            structured_search=self.structured_search,
            pagination=self.pagination,
            facets=self.facets,
            direct_manifest_resolution=self.direct_manifest_resolution and self.resolve_manifest,
            thumbnails=self.thumbnails,
            ocr_signal=self.ocr_signal,
            image_availability=self.image_availability,
            runtime_detection=self.runtime_detection,
            protocol_family=self.protocol_family,
        )


class RuntimeCapabilities(BaseModel):
    """Normalized capability set used for declared/detected/effective snapshots."""

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


class SourceDescriptor(BaseModel):
    """Source metadata exposed through /api/sources."""

    name: str
    label: str
    source_type: str
    capabilities: SourceCapabilities
    healthy: bool
    notes: str | None = None

    declared_capabilities: RuntimeCapabilities
    detected_capabilities: RuntimeCapabilities | None = None
    effective_capabilities: RuntimeCapabilities

    probe_status: ProbeStatus
    probe_message: str | None = None
    probe_timestamp: datetime | None = None
    probe_source: str | None = None
    supports_runtime_detection: bool = False
    capability_warnings: list[str] = Field(default_factory=list)


class SourcesResponse(BaseModel):
    """Response payload for source listing endpoint."""

    sources: list[SourceDescriptor] = Field(default_factory=list)
