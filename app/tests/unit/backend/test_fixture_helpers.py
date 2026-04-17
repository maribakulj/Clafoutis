"""Tests for FixtureConnectorMixin helpers."""

from app.connectors.base import FixtureConnectorMixin


class _Dummy(FixtureConnectorMixin):
    name = "dummy"
    label = "Dummy"


def test_resolve_manifest_from_fixtures_returns_none_when_fixture_has_no_manifest() -> None:
    helper = _Dummy()
    fixtures: list[dict[str, object]] = [
        {"record_url": "https://example.org/a", "manifest_url": None},
        {"record_url": "https://example.org/b"},  # no manifest_url key
    ]

    assert helper._resolve_manifest_from_fixtures("https://example.org/a", fixtures) is None
    assert helper._resolve_manifest_from_fixtures("https://example.org/b", fixtures) is None


def test_resolve_manifest_from_fixtures_returns_url_when_present() -> None:
    helper = _Dummy()
    fixtures: list[dict[str, object]] = [
        {"record_url": "https://example.org/a", "manifest_url": "https://example.org/a/manifest"},
    ]

    assert (
        helper._resolve_manifest_from_fixtures("https://example.org/a", fixtures)
        == "https://example.org/a/manifest"
    )


def test_resolve_manifest_from_fixtures_returns_none_for_unknown_url() -> None:
    helper = _Dummy()
    fixtures: list[dict[str, object]] = [
        {"record_url": "https://example.org/a", "manifest_url": "https://example.org/a/manifest"},
    ]

    assert helper._resolve_manifest_from_fixtures("https://example.org/missing", fixtures) is None
