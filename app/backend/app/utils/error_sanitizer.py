"""Utilities to strip sensitive data from error messages before returning them."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SENSITIVE_QUERY_KEYS = frozenset(
    {
        "wskey",
        "api_key",
        "apikey",
        "key",
        "token",
        "access_token",
        "auth",
        "authorization",
        "password",
    }
)

_URL_PATTERN = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)


def _redact_url(url: str) -> str:
    """Remove sensitive query parameters and credentials from a URL."""

    try:
        parts = urlsplit(url)
    except ValueError:
        return url

    netloc = parts.netloc
    if "@" in netloc:
        netloc = netloc.split("@", 1)[1]

    if parts.query:
        pairs = parse_qsl(parts.query, keep_blank_values=True)
        pairs = [
            (key, "***" if key.lower() in _SENSITIVE_QUERY_KEYS else value)
            for key, value in pairs
        ]
        query = urlencode(pairs)
    else:
        query = parts.query

    return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))


def sanitize_error_message(message: object) -> str:
    """Return a safe string representation with URL secrets redacted."""

    text = str(message)
    return _URL_PATTERN.sub(lambda m: _redact_url(m.group(0)), text)
