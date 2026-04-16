"""Tests for ItemService."""

import asyncio

import pytest
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.services.item_service import ItemService
from app.utils.errors import BadRequestError, NotFoundError


def _make_service() -> ItemService:
    registry = ConnectorRegistry()
    registry.register(MockConnector())
    return ItemService(registry)


def test_get_item_returns_normalized_item() -> None:
    service = _make_service()
    item = asyncio.run(service.get_item("mock:ms-1"))
    assert item.source == "mock"
    assert item.source_item_id == "ms-1"


def test_get_item_rejects_invalid_format() -> None:
    service = _make_service()
    with pytest.raises(BadRequestError):
        asyncio.run(service.get_item("no-colon"))


def test_get_item_unknown_source() -> None:
    service = _make_service()
    with pytest.raises(NotFoundError, match="Unknown source"):
        asyncio.run(service.get_item("unknown:id"))


def test_get_item_not_found() -> None:
    service = _make_service()
    with pytest.raises(NotFoundError, match="not found"):
        asyncio.run(service.get_item("mock:does-not-exist"))
