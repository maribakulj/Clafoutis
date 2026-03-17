"""Normalized item model shared by all connectors and APIs."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NormalizedItem(BaseModel):
    """Normalized representation of an item from any source."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Global identifier in format source:source_item_id.")
    source: str
    source_label: str
    source_item_id: str
    title: str
    creators: list[str] = Field(default_factory=list)
    date_display: str | None = None
    object_type: str = "other"
    institution: str | None = None
    thumbnail_url: str | None = None
    record_url: str | None = None
    manifest_url: str | None = None
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
