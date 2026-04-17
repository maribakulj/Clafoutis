import pytest
from app.utils.errors import BadRequestError
from app.utils.url_validation import validate_http_url


def test_validate_http_url_accepts_public_https() -> None:
    assert validate_http_url("https://gallica.bnf.fr/ark:/12148/btv1b55002481n")


def test_validate_http_url_rejects_localhost() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("http://localhost:8000/test")


def test_validate_http_url_rejects_ip6_localhost_alias() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("http://ip6-localhost/")


def test_validate_http_url_rejects_unsupported_scheme() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("file:///tmp/a")


def test_validate_http_url_rejects_ftp_scheme() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("ftp://example.org/resource")


def test_validate_http_url_rejects_loopback_ipv4() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("http://127.0.0.1/")


def test_validate_http_url_rejects_zero_ipv4() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("http://0.0.0.0/")


def test_validate_http_url_rejects_private_ipv4() -> None:
    for host in ("10.0.0.1", "192.168.1.1", "172.16.0.1", "169.254.169.254"):
        with pytest.raises(BadRequestError):
            validate_http_url(f"http://{host}/")


def test_validate_http_url_rejects_ipv6_loopback() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("http://[::1]/")


def test_validate_http_url_rejects_ipv4_mapped_ipv6() -> None:
    # ::ffff:127.0.0.1 should be normalized to 127.0.0.1 and rejected.
    with pytest.raises(BadRequestError):
        validate_http_url("http://[::ffff:127.0.0.1]/")


def test_validate_http_url_rejects_credentials_in_url() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("https://user:pass@example.org/")


def test_validate_http_url_rejects_disallowed_port() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("https://example.org:22/")


def test_validate_http_url_rejects_overlong_url() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("https://example.org/" + "a" * 3000)


def test_validate_http_url_rejects_empty() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("")


def test_validate_http_url_rejects_missing_host() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("https:///path")
