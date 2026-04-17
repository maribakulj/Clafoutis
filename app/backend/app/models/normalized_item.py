"""Normalized item model shared by all connectors and APIs."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NormalizedItem(BaseModel):
    """Normalized representation of an item from any source.

    The field set mirrors specs §11.1. Every field has a safe default so
    connectors can populate only what the source actually exposes. New
    fields added in Phase 7 (subtitle, description, languages, rights,
    license, collection, date_sort, preview_image_url,
    iiif_image_service_url) are opt-in and unset by default, which keeps
    existing fixtures and the API contract backward-compatible.
    """

    model_config = ConfigDict(extra="forbid")

    # Identity.
    id: str = Field(description="Global identifier in format source:source_item_id.")
    source: str
    source_label: str
    source_item_id: str

    # Core bibliographic metadata.
    title: str
    subtitle: str | None = None
    creators: list[str] = Field(default_factory=list)
    date_display: str | None = None
    date_sort: str | None = None
    languages: list[str] = Field(default_factory=list)
    object_type: str = "other"
    description: str | None = None

    # Provenance and rights.
    institution: str | None = None
    collection: str | None = None
    rights: str | None = None
    license: str | None = None

    # Media and access URLs.
    thumbnail_url: str | None = None
    preview_image_url: str | None = None
    record_url: str | None = None
    manifest_url: str | None = None
    iiif_image_service_url: str | None = None

    # Capability signals.
    has_iiif_manifest: bool = False
    has_images: bool = False
    has_ocr: bool = False
    availability: str = "unknown"
    relevance_score: float = 0.0
    normalization_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_global_id(self) -> "NormalizedItem":
        """Ensure `id` follows the stable MVP rule `source:source_item_id`."""

        expected_id = f"{self.source}:{self.source_item_id}"
        if self.id != expected_id:
            raise ValueError("id must match source:source_item_id")
        return self
