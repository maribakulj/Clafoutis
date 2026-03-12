import asyncio

from app.connectors.mock_connector import MockConnector
from app.models.source_models import RuntimeCapabilities
from app.utils.probing.prober import CapabilityProber


def _declared_runtime() -> RuntimeCapabilities:
    return RuntimeCapabilities(
        free_text_search=True,
        structured_search=False,
        pagination=True,
        facets=False,
        direct_manifest_resolution=True,
        thumbnails=False,
        ocr_signal=False,
        image_availability=True,
        runtime_detection=True,
        protocol_family="sru",
    )


def test_merge_capabilities_with_conflicts() -> None:
    prober = CapabilityProber()
    declared = _declared_runtime()
    detected = RuntimeCapabilities(
        free_text_search=True,
        structured_search=True,
        pagination=True,
        facets=True,
        direct_manifest_resolution=False,
        thumbnails=False,
        ocr_signal=False,
        image_availability=True,
        runtime_detection=True,
        protocol_family="sru",
    )

    effective, warnings = prober.merge_capabilities(declared, detected)

    assert effective.structured_search is True
    assert effective.facets is True
    assert effective.direct_manifest_resolution is False
    assert warnings


def test_probe_not_supported_when_runtime_detection_disabled() -> None:
    prober = CapabilityProber()
    connector = MockConnector()
    declared = RuntimeCapabilities(
        free_text_search=True,
        structured_search=False,
        pagination=True,
        facets=False,
        direct_manifest_resolution=True,
        thumbnails=False,
        ocr_signal=True,
        image_availability=True,
        runtime_detection=False,
        protocol_family="mock",
    )

    snapshot = asyncio.run(prober.probe(connector, declared))

    assert snapshot.probe_status == "not_supported"
    assert snapshot.detected_capabilities is None


def test_probe_supported(monkeypatch) -> None:
    prober = CapabilityProber()
    declared = _declared_runtime()

    detected = RuntimeCapabilities(
        free_text_search=True,
        structured_search=True,
        pagination=True,
        facets=False,
        direct_manifest_resolution=False,
        thumbnails=False,
        ocr_signal=False,
        image_availability=True,
        runtime_detection=True,
        protocol_family="sru",
    )

    async def _supported_probe(_: object) -> tuple[RuntimeCapabilities, str]:
        return detected, "ok"

    monkeypatch.setattr(prober, "_probe_sru_connector", _supported_probe)

    class _SRUConnector:
        name = "gallica"

    snapshot = asyncio.run(prober.probe(_SRUConnector(), declared))

    assert snapshot.probe_status == "supported"
    assert snapshot.detected_capabilities is not None
    assert snapshot.effective_capabilities.structured_search is True


def test_probe_timeout(monkeypatch) -> None:
    prober = CapabilityProber()
    declared = _declared_runtime()

    async def _timeout_probe(_: object) -> tuple[RuntimeCapabilities, str]:
        raise TimeoutError("boom")

    monkeypatch.setattr(prober, "_probe_sru_connector", _timeout_probe)

    class _SRUConnector:
        name = "gallica"

    snapshot = asyncio.run(prober.probe(_SRUConnector(), declared))
    assert snapshot.probe_status == "timeout"
    assert snapshot.detected_capabilities is None


def test_probe_failed(monkeypatch) -> None:
    prober = CapabilityProber()
    declared = _declared_runtime()

    async def _failed_probe(_: object) -> tuple[RuntimeCapabilities, str]:
        raise RuntimeError("failed")

    monkeypatch.setattr(prober, "_probe_sru_connector", _failed_probe)

    class _SRUConnector:
        name = "gallica"

    snapshot = asyncio.run(prober.probe(_SRUConnector(), declared))
    assert snapshot.probe_status == "failed"
    assert "failed" in (snapshot.probe_message or "")
