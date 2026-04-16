import pytest
from app.utils.errors import BadRequestError
from app.utils.url_validation import validate_http_url


def test_validate_http_url_rejects_localhost() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("http://localhost:8000/test")


def test_validate_http_url_rejects_unsupported_scheme() -> None:
    with pytest.raises(BadRequestError):
        validate_http_url("file:///tmp/a")
