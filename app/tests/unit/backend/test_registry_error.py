"""Regression: ConnectorRegistry.get raises NotFoundError, not KeyError."""

import pytest
from app.connectors.registry import ConnectorRegistry
from app.utils.errors import NotFoundError


def test_registry_get_unknown_raises_not_found_error() -> None:
    registry = ConnectorRegistry()
    with pytest.raises(NotFoundError, match="Unknown source"):
        registry.get("nope")
