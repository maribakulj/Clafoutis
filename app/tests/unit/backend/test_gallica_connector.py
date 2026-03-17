import asyncio

from app.config.settings import settings
from app.connectors.gallica import GallicaConnector


def test_gallica_search_returns_normalized_items_in_fixture_mode() -> None:
    settings.gallica_use_fixtures = True
    connector = GallicaConnector()

    response = asyncio.run(connector.search(query="dante", filters={}, page=1, page_size=10))

    assert response.results
    first = response.results[0]
    assert first.source == "gallica"
    assert first.id.startswith("gallica:")
    assert first.record_url is not None
    assert first.manifest_url is not None
    assert first.has_iiif_manifest is True


def test_gallica_resolve_manifest_from_record_url() -> None:
    connector = GallicaConnector()

    resolved = asyncio.run(
        connector.resolve_manifest(record_url="https://gallica.bnf.fr/ark:/12148/bpt6k1512248m")
    )

    assert resolved == "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k1512248m/manifest.json"
