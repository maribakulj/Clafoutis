"""URL validation helpers for import and manifest resolution endpoints."""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

from app.utils.errors import BadRequestError

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_PORTS: frozenset[int] = frozenset({80, 443, 8080, 8443})
_BLOCKED_HOSTS = {"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"}


def _normalize_ip(ip_text: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Parse and normalize an IP address, unwrapping IPv4-mapped IPv6."""

    ip_obj = ipaddress.ip_address(ip_text)
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None:
        return ip_obj.ipv4_mapped
    return ip_obj


def _is_forbidden_ip(ip_text: str) -> bool:
    """Return True when an IP points to a local/private/non-routable range."""

    ip_obj = _normalize_ip(ip_text)
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
    if not lowered:
        raise BadRequestError("URL host is empty")
    if lowered in _BLOCKED_HOSTS:
        raise BadRequestError("URL host is not allowed")

    # Strip surrounding brackets for IPv6 literals (urlparse keeps them off hostname, defensive).
    if lowered.startswith("[") and lowered.endswith("]"):
        lowered = lowered[1:-1]

    # Direct IP host (including decimal, hex, octal variants parsed by ipaddress).
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
        ip_text = str(info[4][0])
        # IPv6 addresses from getaddrinfo may include scope suffix (e.g. fe80::1%eth0).
        ip_text = ip_text.split("%", 1)[0]
        if _is_forbidden_ip(ip_text):
            raise BadRequestError("URL host is not allowed")


def validate_http_url(url: str) -> str:
    """Validate URL syntax and enforce SSRF restrictions on host, scheme, port."""

    if not isinstance(url, str) or not url:
        raise BadRequestError("URL must be a non-empty string")
    if len(url) > 2048:
        raise BadRequestError("URL is too long")

    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise BadRequestError("URL scheme must be http or https")
    if not parsed.netloc:
        raise BadRequestError("URL must contain a host")
    if not parsed.hostname:
        raise BadRequestError("URL must contain a valid host")
    if parsed.username or parsed.password:
        raise BadRequestError("URL must not contain credentials")

    try:
        port = parsed.port
    except ValueError as err:
        raise BadRequestError("URL port is invalid") from err
    if port is not None and port not in _ALLOWED_PORTS:
        raise BadRequestError("URL port is not allowed")

    _validate_host_ssrf(parsed.hostname)
    return url
