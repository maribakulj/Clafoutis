"""Tests for Gallica XML parsing robustness."""

import defusedxml.ElementTree as ET
from app.connectors.gallica.connector import GallicaConnector

SRU_RESPONSE_WITH_DUPLICATES = """<?xml version='1.0' encoding='UTF-8'?>
<srw:searchRetrieveResponse xmlns:srw='http://www.loc.gov/zing/srw/'
                            xmlns:dc='http://purl.org/dc/elements/1.1/'>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <dc:title>Livre d'heures</dc:title>
        <dc:title>Livre d'heures</dc:title>
        <dc:creator>Anonyme</dc:creator>
        <dc:identifier>https://gallica.bnf.fr/ark:/12148/btv1b55002481n</dc:identifier>
        <dc:identifier>ark:/12148/btv1b55002481n</dc:identifier>
        <dc:type>manuscrit</dc:type>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>
"""


def test_gallica_parsing_matches_namespaced_record_tag() -> None:
    connector = GallicaConnector()
    root = ET.fromstring(SRU_RESPONSE_WITH_DUPLICATES)

    records = list(root.iter("{http://www.loc.gov/zing/srw/}record"))
    assert len(records) == 1

    item = connector._map_record(records[0], 0)
    assert item.source_item_id == "ark:/12148/btv1b55002481n"
    assert item.record_url == "https://gallica.bnf.fr/ark:/12148/btv1b55002481n"
    assert item.manifest_url == (
        "https://gallica.bnf.fr/iiif/ark:/12148/btv1b55002481n/manifest.json"
    )


def test_gallica_parsing_dedupes_duplicate_dc_values() -> None:
    connector = GallicaConnector()
    root = ET.fromstring(SRU_RESPONSE_WITH_DUPLICATES)
    record = next(root.iter("{http://www.loc.gov/zing/srw/}record"))

    dc = connector._extract_dc_values(record)

    # Duplicate titles collapsed.
    assert dc["title"] == ["Livre d'heures"]
    # Both identifiers kept (different strings) but URL-first heuristic still picks the HTTP one.
    assert "https://gallica.bnf.fr/ark:/12148/btv1b55002481n" in dc["identifier"]
    assert "ark:/12148/btv1b55002481n" in dc["identifier"]


def test_gallica_record_url_prefers_http_over_bare_ark() -> None:
    connector = GallicaConnector()
    root = ET.fromstring(SRU_RESPONSE_WITH_DUPLICATES)
    record = next(root.iter("{http://www.loc.gov/zing/srw/}record"))

    item = connector._map_record(record, 0)

    assert item.record_url is not None
    assert item.record_url.startswith("https://")
