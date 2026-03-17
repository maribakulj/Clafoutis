"""Settings environment aliases tests."""

from app.config.settings import Settings


def test_europeana_api_key_reads_clafoutis_prefixed_env(monkeypatch) -> None:
    """Europeana API key should be loaded from CLAFOUTIS_EUROPEANA_API_KEY first."""

    monkeypatch.setenv("CLAFOUTIS_EUROPEANA_API_KEY", "prefixed-key")
    monkeypatch.delenv("EUROPEANA_API_KEY", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)

    loaded = Settings()

    assert loaded.europeana_api_key == "prefixed-key"


def test_europeana_api_key_accepts_hf_token_fallback(monkeypatch) -> None:
    """HF Space secret HF_TOKEN should be accepted as a fallback for Europeana wskey."""

    monkeypatch.delenv("CLAFOUTIS_EUROPEANA_API_KEY", raising=False)
    monkeypatch.delenv("EUROPEANA_API_KEY", raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf-secret-token")

    loaded = Settings()

    assert loaded.europeana_api_key == "hf-secret-token"


def test_bodleian_use_fixtures_accepts_descriptive_value(monkeypatch) -> None:
    """Boolean settings should stay robust with descriptive env values from platform UIs."""

    monkeypatch.setenv(
        "CLAFOUTIS_BODLEIAN_USE_FIXTURES",
        "Use fixture data for Bodleian connector to keep the demo stable",
    )

    loaded = Settings()

    assert loaded.bodleian_use_fixtures is True


def test_serve_frontend_accepts_descriptive_value(monkeypatch) -> None:
    """Frontend serving flag should tolerate descriptive values from Space UI."""

    monkeypatch.setenv("CLAFOUTIS_SERVE_FRONTEND", "Serve the built frontend from the backend")

    loaded = Settings()

    assert loaded.serve_frontend_enabled is True
