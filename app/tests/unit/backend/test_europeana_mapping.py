"""Tests for Europeana live record mapping heuristics."""

from app.connectors.europeana.connector import EuropeanaConnector


def test_europeana_no_manifest_when_edm_is_image_url() -> None:
    connector = EuropeanaConnector()
    record = {
        "id": "/2021664/dante_ms_1",
        "edmIsShownBy": ["https://example.org/image.jpg"],
        "guid": "https://www.europeana.eu/en/item/2021664/dante_ms_1",
        "title": ["Dante"],
    }

    item = connector._map_live_record(record, 0)

    assert item.manifest_url is None
    assert item.has_iiif_manifest is False


def test_europeana_manifest_detected_when_url_ends_with_manifest() -> None:
    connector = EuropeanaConnector()
    record = {
        "id": "/2021664/dante_ms_1",
        "edmIsShownBy": ["https://iiif.europeana.eu/presentation/2021664/dante_ms_1/manifest"],
        "title": ["Dante"],
    }

    item = connector._map_live_record(record, 0)

    assert item.manifest_url == (
        "https://iiif.europeana.eu/presentation/2021664/dante_ms_1/manifest"
    )


def test_europeana_date_display_prefers_year_over_ingestion_epoch() -> None:
    connector = EuropeanaConnector()
    record = {
        "id": "/2021664/x",
        "year": ["1450"],
        "timestamp_created_epoch": 1700000000000,
        "title": ["t"],
    }

    item = connector._map_live_record(record, 0)
    assert item.date_display == "1450"


def test_europeana_date_display_falls_back_through_alternatives() -> None:
    connector = EuropeanaConnector()
    record = {
        "id": "/2021664/x",
        "dcDate": ["circa 1500"],
        "title": ["t"],
    }

    item = connector._map_live_record(record, 0)
    assert item.date_display == "circa 1500"


def test_europeana_resolve_manifest_does_not_fabricate() -> None:
    """The connector must not invent a manifest URL from a plain record URL."""

    import asyncio

    connector = EuropeanaConnector()
    resolved = asyncio.run(
        connector.resolve_manifest(
            record_url="https://www.europeana.eu/en/item/unknown/record_42"
        )
    )
    assert resolved is None
