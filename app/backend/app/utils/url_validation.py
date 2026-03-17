"""URL validation helpers for import and manifest resolution endpoints."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.utils.errors import BadRequestError


def validate_http_url(url: str) -> str:
    """Validate URL scheme/host and apply basic SSRF protections for MVP."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise BadRequestError("URL scheme must be http or https")

    if not parsed.netloc or parsed.hostname is None:
        raise BadRequestError("URL must contain a valid host")

    _reject_local_hostnames(parsed.hostname)
    _reject_private_or_local_ip_literals(parsed.hostname)
    _reject_hostnames_resolving_to_private_or_local_ips(parsed.hostname)

    return url


def _reject_local_hostnames(hostname: str) -> None:
    lowered = hostname.lower()
    blocked = {"localhost", "localhost.localdomain"}
    if lowered in blocked:
        raise BadRequestError("Local hosts are not allowed")


def _reject_private_or_local_ip_literals(hostname: str) -> None:
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
        raise BadRequestError("Private or local IPs are not allowed")


def _reject_hostnames_resolving_to_private_or_local_ips(hostname: str) -> None:
    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # If hostname cannot be resolved, keep request valid and let downstream
        # connector/network errors explain the failure.
        return

    for info in addrinfos:
        raw_ip = info[4][0]
        ip = ipaddress.ip_address(raw_ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
            raise BadRequestError("Resolved host points to a private or local IP")
