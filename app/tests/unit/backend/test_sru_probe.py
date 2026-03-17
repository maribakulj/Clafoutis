from pathlib import Path

from app.utils.probing.sru_probe import SRUCapabilityProbe


def test_parse_sru_explain_fixture() -> None:
    fixture = Path("app/tests/unit/backend/fixtures/sru_explain.xml").read_text(encoding="utf-8")

    probe = SRUCapabilityProbe()
    capabilities = probe.parse_explain(fixture)

    assert capabilities.protocol_family == "sru"
    assert capabilities.runtime_detection is True
    assert capabilities.structured_search is True
    assert capabilities.free_text_search is True
