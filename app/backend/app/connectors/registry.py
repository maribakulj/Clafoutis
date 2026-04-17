"""Registry storing available connectors."""

from app.connectors.base import BaseConnector
from app.utils.errors import NotFoundError


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
        """Return connector instance for the provided name.

        Raises ``NotFoundError`` when the name is unknown so callers get a
        structured domain error rather than a raw ``KeyError``.
        """

        try:
            return self._connectors[name]
        except KeyError as err:
            raise NotFoundError(f"Unknown source '{name}'") from err

    def has(self, name: str) -> bool:
        """Return whether a connector with the given name is registered."""

        return name in self._connectors

    def list_connectors(self) -> list[BaseConnector]:
        """Return registered connector instances."""

        return [self._connectors[name] for name in self.list_names()]
