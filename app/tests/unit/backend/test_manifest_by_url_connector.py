import asyncio

from app.connectors.manifest_by_url_connector import ManifestByUrlConnector


def test_manifest_by_url_connector_detects_direct_manifest() -> None:
    connector = ManifestByUrlConnector()

    resolved = asyncio.run(
        connector.resolve_manifest(
            record_url="https://example.org/iiif/manifest/123",
        )
    )

    assert resolved == "https://example.org/iiif/manifest/123"


def test_manifest_by_url_connector_generates_notice_candidates() -> None:
    connector = ManifestByUrlConnector()

    resolved = asyncio.run(connector.resolve_manifest(record_url="https://example.org/item/123"))

    assert resolved == "https://example.org/item/123/manifest"
