"""Tests for URL-aware error message sanitizer."""

from app.utils.error_sanitizer import sanitize_error_message


def test_sanitize_redacts_wskey_query_param() -> None:
    message = (
        "HTTPStatusError: "
        "https://api.europeana.eu/record/v2/search.json?wskey=secret123&query=dante"
    )
    sanitized = sanitize_error_message(message)
    assert "secret123" not in sanitized
    assert "wskey=%2A%2A%2A" in sanitized or "wskey=***" in sanitized


def test_sanitize_redacts_credentials_in_url() -> None:
    message = "timeout: https://user:pass@example.org/path"
    sanitized = sanitize_error_message(message)
    assert "user:pass" not in sanitized
    assert "example.org" in sanitized


def test_sanitize_redacts_multiple_sensitive_keys() -> None:
    message = "error: https://api.example.com/?api_key=abc&token=xyz&q=test"
    sanitized = sanitize_error_message(message)
    assert "abc" not in sanitized
    assert "xyz" not in sanitized
    assert "q=test" in sanitized


def test_sanitize_passes_through_safe_urls() -> None:
    message = "network failed: https://gallica.bnf.fr/ark:/12148/bpt6k1512248m"
    sanitized = sanitize_error_message(message)
    assert "gallica.bnf.fr" in sanitized


def test_sanitize_accepts_non_string_input() -> None:
    sanitized = sanitize_error_message(RuntimeError("boom"))
    assert "boom" in sanitized
