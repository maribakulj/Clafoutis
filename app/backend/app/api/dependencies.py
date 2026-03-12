"""Dependency providers for API routes."""

from functools import lru_cache

from app.connectors.bodleian import BodleianConnector
from app.connectors.europeana import EuropeanaConnector
from app.connectors.gallica import GallicaConnector
from app.connectors.manifest_by_url_connector import ManifestByUrlConnector
from app.connectors.mock_connector import MockConnector
from app.connectors.registry import ConnectorRegistry
from app.services.import_service import ImportService
from app.services.item_service import ItemService
from app.services.manifest_resolver import ManifestResolver
from app.services.search_orchestrator import SearchOrchestrator
from app.services.source_service import SourceService
from app.utils.probing.prober import CapabilityProber


@lru_cache(maxsize=1)
def get_registry() -> ConnectorRegistry:
    """Create and cache connector registry with MVP connectors."""

    registry = ConnectorRegistry()
    registry.register(MockConnector())
    registry.register(GallicaConnector())
    registry.register(BodleianConnector())
    registry.register(EuropeanaConnector())
    registry.register(ManifestByUrlConnector())
    return registry


@lru_cache(maxsize=1)
def get_capability_prober() -> CapabilityProber:
    """Create and cache capability prober with in-memory cache."""

    return CapabilityProber()


def get_search_orchestrator() -> SearchOrchestrator:
    """Return orchestrator instance wired with connector registry."""

    return SearchOrchestrator(get_registry())


@lru_cache(maxsize=1)
def get_source_service() -> SourceService:
    """Return source service instance."""

    return SourceService(get_registry(), get_capability_prober())


def get_item_service() -> ItemService:
    """Return item service instance."""

    return ItemService(get_registry())


def get_manifest_resolver() -> ManifestResolver:
    """Return manifest resolver instance."""

    return ManifestResolver(get_registry())


def get_import_service() -> ImportService:
    """Return import service instance."""

    return ImportService(get_registry())
