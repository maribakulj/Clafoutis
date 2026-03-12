from app.utils.errors import BadRequestError
from app.utils.url_validation import validate_http_url


def test_validate_http_url_rejects_localhost() -> None:
    try:
        validate_http_url("http://localhost:8000/test")
        assert False, "localhost should be rejected"
    except BadRequestError:
        pass


def test_validate_http_url_rejects_unsupported_scheme() -> None:
    try:
        validate_http_url("file:///tmp/a")
        assert False, "unsupported scheme should be rejected"
    except BadRequestError:
        pass
