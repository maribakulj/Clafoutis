"""Tests for the enriched NormalizedItem field set (specs §11.1)."""

from app.models.normalized_item import NormalizedItem


def test_extended_fields_are_optional_with_safe_defaults() -> None:
    """All new fields must default to None / empty so existing connectors
    keep compiling without mentioning them explicitly."""

    item = NormalizedItem(
        id="mock:x",
        source="mock",
        source_label="Mock",
        source_item_id="x",
        title="t",
    )

    assert item.subtitle is None
    assert item.description is None
    assert item.languages == []
    assert item.rights is None
    assert item.license is None
    assert item.collection is None
    assert item.date_sort is None
    assert item.preview_image_url is None
    assert item.iiif_image_service_url is None


def test_extended_fields_round_trip_through_json() -> None:
    item = NormalizedItem(
        id="mock:x",
        source="mock",
        source_label="Mock",
        source_item_id="x",
        title="Book of Hours",
        subtitle="Latin use of Rome",
        description="A richly illuminated 15th-century manuscript",
        languages=["lat"],
        rights="Public domain",
        license="CC0-1.0",
        collection="Western manuscripts",
        date_sort="1450",
        preview_image_url="https://example.org/p.jpg",
        iiif_image_service_url="https://example.org/iiif/image",
    )

    dumped = item.model_dump()
    assert dumped["subtitle"] == "Latin use of Rome"
    assert dumped["languages"] == ["lat"]
    assert dumped["collection"] == "Western manuscripts"
