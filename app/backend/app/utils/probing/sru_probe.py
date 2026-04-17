"""SRU Explain capability probing helpers."""

from __future__ import annotations

from urllib.parse import urlencode

import defusedxml.ElementTree as SafeET

from app.config.settings import settings
from app.models.source_models import RuntimeCapabilities
from app.utils.http_client import build_async_client

FIXTURE_SRU_EXPLAIN = """<?xml version='1.0' encoding='UTF-8'?>
<srw:explainResponse xmlns:srw='http://www.loc.gov/zing/srw/' xmlns:zr='http://explain.z3950.org/dtd/2.0/'>
  <srw:record>
    <srw:recordData>
      <zr:explain>
        <zr:serverInfo protocol='SRU' version='1.2'/>
        <zr:indexInfo>
          <zr:index>
            <zr:title>dc.title</zr:title>
          </zr:index>
          <zr:index>
            <zr:title>dc.creator</zr:title>
          </zr:index>
        </zr:indexInfo>
        <zr:schemaInfo>
          <zr:schema identifier='oai_dc'/>
        </zr:schemaInfo>
      </zr:explain>
    </srw:recordData>
  </srw:record>
</srw:explainResponse>
"""


class SRUCapabilityProbe:
    """Probe SRU sources through Explain and infer runtime capabilities."""

    probe_source = "sru_explain"

    async def probe(self, endpoint: str) -> tuple[RuntimeCapabilities, str]:
        """Fetch and parse SRU Explain response for a given endpoint."""

        xml_payload = await self.fetch_explain(endpoint)
        capabilities = self.parse_explain(xml_payload)
        return capabilities, "SRU Explain parsed successfully"

    async def fetch_explain(self, endpoint: str) -> str:
        """Return Explain payload from fixture or live endpoint."""

        if settings.capability_probe_use_fixtures:
            return FIXTURE_SRU_EXPLAIN

        params = urlencode({"version": "1.2", "operation": "explain"})
        explain_url = f"{endpoint}?{params}"

        async with build_async_client() as client:
            response = await client.get(explain_url, timeout=settings.capability_probe_timeout_seconds)
            response.raise_for_status()
            return response.text

    def parse_explain(self, xml_payload: str) -> RuntimeCapabilities:
        """Infer a minimal runtime capability set from Explain XML payload."""

        root = SafeET.fromstring(xml_payload)
        titles = [
            (node.text or "").strip().lower()
            for node in root.iter()
            if node.tag.endswith("title") and node.text
        ]

        has_structured = any(title.startswith("dc.") or title.startswith("cql.") for title in titles)

        return RuntimeCapabilities(
            free_text_search=True,
            structured_search=has_structured,
            pagination=True,
            facets=False,
            direct_manifest_resolution=False,
            thumbnails=False,
            ocr_signal=False,
            image_availability=True,
            runtime_detection=True,
            protocol_family="sru",
        )
