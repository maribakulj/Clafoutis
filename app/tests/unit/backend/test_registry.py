from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry


def test_registry_register_and_get() -> None:
    registry = ConnectorRegistry()
    connector = MockConnector()
    registry.register(connector)
    assert registry.list_names() == ["mock"]
    assert registry.get("mock") is connector
