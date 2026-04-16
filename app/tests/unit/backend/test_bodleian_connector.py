import asyncio

from app.config.settings import settings
from app.connectors.bodleian import BodleianConnector


def test_bodleian_search_returns_normalized_items_in_fixture_mode() -> None:
    original = settings.bodleian_use_fixtures
    settings.bodleian_use_fixtures = True
    try:
        connector = BodleianConnector()
        response = asyncio.run(connector.search(query="dante", filters={}, page=1, page_size=10))

        assert response.results
        first = response.results[0]
        assert first.source == "bodleian"
        assert first.id.startswith("bodleian:")
        assert first.manifest_url is not None
    finally:
        settings.bodleian_use_fixtures = original


def test_bodleian_resolve_manifest_from_record_url() -> None:
    connector = BodleianConnector()

    resolved = asyncio.run(
        connector.resolve_manifest(
            record_url="https://digital.bodleian.ox.ac.uk/objects/bodleian-ms-dante-1/"
        )
    )

    assert resolved == "https://iiif.bodleian.ox.ac.uk/iiif/manifest/bodleian-ms-dante-1.json"
