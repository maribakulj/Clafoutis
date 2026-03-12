"""Runtime capability probing orchestration and merge logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from app.config.settings import settings
from app.connectors.base import BaseConnector
from app.models.source_models import ProbeStatus, RuntimeCapabilities
from app.utils.probing.sru_probe import SRUCapabilityProbe


@dataclass
class ProbeSnapshot:
    """Cached runtime probe information for one source."""

    detected_capabilities: RuntimeCapabilities | None
    effective_capabilities: RuntimeCapabilities
    probe_status: ProbeStatus
    probe_message: str | None
    probe_timestamp: datetime | None
    probe_source: str | None
    supports_runtime_detection: bool
    capability_warnings: list[str]


class CapabilityProber:
    """Resolve runtime capabilities with graceful degradation and in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, ProbeSnapshot] = {}
        self._sru_probe = SRUCapabilityProbe()

    def _is_cache_valid(self, snapshot: ProbeSnapshot) -> bool:
        if not snapshot.probe_timestamp:
            return False
        ttl = timedelta(seconds=settings.capability_probe_cache_ttl_seconds)
        return datetime.now(timezone.utc) - snapshot.probe_timestamp <= ttl

    def merge_capabilities(
        self,
        declared: RuntimeCapabilities,
        detected: RuntimeCapabilities | None,
    ) -> tuple[RuntimeCapabilities, list[str]]:
        """Merge declared and detected capabilities and keep divergence warnings."""

        warnings: list[str] = []
        if detected is None:
            return declared, warnings

        merged_data = declared.model_dump()
        detected_data = detected.model_dump()
        for key, detected_value in detected_data.items():
            declared_value = merged_data.get(key)
            if declared_value != detected_value:
                warnings.append(
                    f"capability_conflict:{key}:declared={declared_value}:detected={detected_value}"
                )
            merged_data[key] = detected_value

        merged_data["runtime_detection"] = declared.runtime_detection or detected.runtime_detection
        return RuntimeCapabilities(**merged_data), warnings

    async def probe(
        self,
        connector: BaseConnector,
        declared: RuntimeCapabilities,
    ) -> ProbeSnapshot:
        """Probe connector runtime capabilities and return merged snapshot."""

        cached = self._cache.get(connector.name)
        if cached and self._is_cache_valid(cached):
            return cached

        now = datetime.now(timezone.utc)

        if not settings.enable_capability_probing:
            effective, warnings = self.merge_capabilities(declared, None)
            snapshot = ProbeSnapshot(
                detected_capabilities=None,
                effective_capabilities=effective,
                probe_status="skipped",
                probe_message="runtime probing disabled by settings",
                probe_timestamp=now,
                probe_source=None,
                supports_runtime_detection=declared.runtime_detection,
                capability_warnings=warnings,
            )
            self._cache[connector.name] = snapshot
            return snapshot

        if declared.protocol_family != "sru" or not declared.runtime_detection:
            effective, warnings = self.merge_capabilities(declared, None)
            snapshot = ProbeSnapshot(
                detected_capabilities=None,
                effective_capabilities=effective,
                probe_status="not_supported",
                probe_message="runtime probing not supported for this source",
                probe_timestamp=now,
                probe_source=None,
                supports_runtime_detection=False,
                capability_warnings=warnings,
            )
            self._cache[connector.name] = snapshot
            return snapshot

        try:
            detected, message = await self._probe_sru_connector(connector)
            effective, warnings = self.merge_capabilities(declared, detected)
            snapshot = ProbeSnapshot(
                detected_capabilities=detected,
                effective_capabilities=effective,
                probe_status="supported",
                probe_message=message,
                probe_timestamp=now,
                probe_source=self._sru_probe.probe_source,
                supports_runtime_detection=True,
                capability_warnings=warnings,
            )
        except TimeoutError:
            effective, warnings = self.merge_capabilities(declared, None)
            snapshot = ProbeSnapshot(
                detected_capabilities=None,
                effective_capabilities=effective,
                probe_status="timeout",
                probe_message="runtime probing timed out",
                probe_timestamp=now,
                probe_source=self._sru_probe.probe_source,
                supports_runtime_detection=True,
                capability_warnings=warnings,
            )
        except (httpx.TimeoutException, httpx.ReadTimeout):
            effective, warnings = self.merge_capabilities(declared, None)
            snapshot = ProbeSnapshot(
                detected_capabilities=None,
                effective_capabilities=effective,
                probe_status="timeout",
                probe_message="runtime probing timed out",
                probe_timestamp=now,
                probe_source=self._sru_probe.probe_source,
                supports_runtime_detection=True,
                capability_warnings=warnings,
            )
        except Exception as exc:  # noqa: BLE001
            effective, warnings = self.merge_capabilities(declared, None)
            snapshot = ProbeSnapshot(
                detected_capabilities=None,
                effective_capabilities=effective,
                probe_status="failed",
                probe_message=f"runtime probing failed: {exc}",
                probe_timestamp=now,
                probe_source=self._sru_probe.probe_source,
                supports_runtime_detection=True,
                capability_warnings=warnings,
            )

        self._cache[connector.name] = snapshot
        return snapshot

    async def _probe_sru_connector(self, connector: BaseConnector) -> tuple[RuntimeCapabilities, str]:
        endpoint = settings.gallica_sru_base_url if connector.name == "gallica" else ""
        if not endpoint:
            raise ValueError("missing SRU endpoint for connector")

        return await self._sru_probe.probe(endpoint)
