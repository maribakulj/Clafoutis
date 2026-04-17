"""Tests for ImportService (generic, no mock-specific branching)."""

import asyncio

import app.services.import_service as import_service_module
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.services.import_service import ImportService


def _make_service() -> ImportService:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    return ImportService(registry)


def _bypass_url_validation(monkeypatch) -> None:
    """Bypass DNS-dependent SSRF validation to keep import tests hermetic."""

    monkeypatch.setattr(import_service_module, "validate_http_url", lambda url: url)


def test_import_returns_item_when_mock_recognizes_record_url(monkeypatch) -> None:
    _bypass_url_validation(monkeypatch)
    service = _make_service()

    response = asyncio.run(service.import_url("https://mock.example.org/items/ms-1"))

    assert response.detected_source == "mock"
    assert response.item is not None
    assert response.item.source_item_id == "ms-1"
    assert response.manifest_url is not None


def test_import_without_matching_record_url_returns_none(monkeypatch) -> None:
    _bypass_url_validation(monkeypatch)
    service = _make_service()

    response = asyncio.run(
        service.import_url("https://mock.example.org/items/does-not-exist")
    )

    assert response.item is None
    assert response.detected_source is None
