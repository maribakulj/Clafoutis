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
