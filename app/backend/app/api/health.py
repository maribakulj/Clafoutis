"""Health endpoint."""

import logging
import time

from fastapi import APIRouter, Depends

from app.api.dependencies import get_registry
from app.connectors.registry import ConnectorRegistry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    registry: ConnectorRegistry = Depends(get_registry),
) -> dict:
    """Return backend health status with per-connector checks."""

    start = time.perf_counter()
    connectors: dict[str, str] = {}

    for connector in registry.list_connectors():
        try:
            result = await connector.healthcheck()
            connectors[connector.name] = result.get("status", "unknown")
        except Exception as exc:
            logger.warning("Healthcheck failed for %s: %s", connector.name, exc)
            connectors[connector.name] = "error"

    all_ok = all(s == "ok" for s in connectors.values())
    duration_ms = int((time.perf_counter() - start) * 1000)

    return {
        "status": "ok" if all_ok else "degraded",
        "connectors": connectors,
        "duration_ms": duration_ms,
    }
