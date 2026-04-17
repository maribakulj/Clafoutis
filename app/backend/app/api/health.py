"""Health endpoints."""

import asyncio
import logging
import time

from fastapi import APIRouter, Depends

from app.api.dependencies import get_registry
from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health/ready")
async def ready() -> dict[str, str]:
    """Liveness/readiness probe for container orchestrators.

    This endpoint does NOT contact any external source. It is safe to poll
    every few seconds (Docker HEALTHCHECK, Kubernetes liveness/readiness)
    without triggering outbound traffic to Gallica/Bodleian/Europeana.
    """

    return {"status": "ok"}


async def _connector_status(connector: BaseConnector) -> tuple[str, str]:
    try:
        result = await connector.healthcheck()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Healthcheck failed for %s: %s", connector.name, exc)
        return connector.name, "error"
    return connector.name, result.get("status", "unknown")


@router.get("/health")
async def health(
    registry: ConnectorRegistry = Depends(get_registry),
) -> dict:
    """Return backend health status with per-connector checks.

    Probes each registered connector in parallel. Use ``/health/ready``
    for container healthchecks; this endpoint is for human monitoring.
    """

    start = time.perf_counter()
    connectors_list = registry.list_connectors()
    statuses = await asyncio.gather(
        *(_connector_status(c) for c in connectors_list),
        return_exceptions=False,
    )
    connectors: dict[str, str] = dict(statuses)

    all_ok = all(s == "ok" for s in connectors.values())
    duration_ms = int((time.perf_counter() - start) * 1000)

    return {
        "status": "ok" if all_ok else "degraded",
        "connectors": connectors,
        "duration_ms": duration_ms,
    }
