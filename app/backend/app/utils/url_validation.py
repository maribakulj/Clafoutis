"""URL validation helpers for import and manifest resolution endpoints."""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

from app.utils.errors import BadRequestError

logger = logging.getLogger(__name__)


def _is_forbidden_ip(ip_text: str) -> bool:
    """Return True when an IP points to a local/private/non-routable range."""

    ip_obj = ipaddress.ip_address(ip_text)
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or ip_obj.is_multicast
        or ip_obj.is_unspecified
    )


def _validate_host_ssrf(host: str) -> None:
    """Reject localhost and hosts resolving to local/private address ranges."""

    lowered = host.strip().lower()
    if lowered in {"localhost", "localhost.localdomain"}:
        raise BadRequestError("URL host is not allowed")

    # Direct IP host.
    try:
        if _is_forbidden_ip(lowered):
            raise BadRequestError("URL host is not allowed")
        return
    except ValueError:
        pass

    # DNS host -- reject if resolution fails (prevents DNS rebinding bypass).
    try:
        infos = socket.getaddrinfo(lowered, None)
    except socket.gaierror:
        logger.warning("DNS resolution failed for host %s, rejecting", lowered)
        raise BadRequestError("URL host could not be resolved") from None

    for info in infos:
        ip_text = info[4][0]
        if _is_forbidden_ip(ip_text):
            raise BadRequestError("URL host is not allowed")


def validate_http_url(url: str) -> str:
    """Validate URL syntax and enforce SSRF restrictions on host and scheme."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise BadRequestError("URL scheme must be http or https")
    if not parsed.netloc:
        raise BadRequestError("URL must contain a host")
    if not parsed.hostname:
        raise BadRequestError("URL must contain a valid host")

    _validate_host_ssrf(parsed.hostname)
    return url
