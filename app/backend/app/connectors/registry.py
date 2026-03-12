"""Registry storing available connectors."""

from app.connectors.base import BaseConnector


class ConnectorRegistry:
    """In-memory registry for connector instances."""

    def __init__(self) -> None:
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        """Register a connector instance by unique connector name."""

        self._connectors[connector.name] = connector

    def list_names(self) -> list[str]:
        """Return sorted connector names."""

        return sorted(self._connectors.keys())

    def get(self, name: str) -> BaseConnector:
        """Return connector instance for the provided name."""

        return self._connectors[name]

    def has(self, name: str) -> bool:
        """Return whether a connector with the given name is registered."""

        return name in self._connectors

    def list_connectors(self) -> list[BaseConnector]:
        """Return registered connector instances."""

        return [self._connectors[name] for name in self.list_names()]
