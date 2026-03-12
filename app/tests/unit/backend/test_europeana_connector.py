import asyncio

from app.config.settings import settings
from app.connectors.europeana import EuropeanaConnector


def test_europeana_search_returns_normalized_items_in_fixture_mode() -> None:
    settings.europeana_use_fixtures = True
    connector = EuropeanaConnector()

    response = asyncio.run(connector.search(query="dante", filters={}, page=1, page_size=10))

    assert response.results
    first = response.results[0]
    assert first.source == "europeana"
    assert first.id.startswith("europeana:")
    assert first.manifest_url is not None


def test_europeana_resolve_manifest_from_record_url() -> None:
    connector = EuropeanaConnector()

    resolved = asyncio.run(
        connector.resolve_manifest(record_url="https://www.europeana.eu/en/item/2021664/dante_ms_1")
    )

    assert resolved == "https://iiif.europeana.eu/presentation/2021664/dante_ms_1/manifest"
