"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend application."""

    app_name: str = "Clafoutis Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    request_timeout_seconds: float = Field(default=8.0, gt=0)
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Connector settings
    gallica_use_fixtures: bool = False
    gallica_sru_base_url: str = "https://gallica.bnf.fr/SRU"
    bodleian_use_fixtures: bool = False
    bodleian_api_base_url: str = "https://api.bodleian.ox.ac.uk/iiif"
    europeana_use_fixtures: bool = False
    europeana_api_base_url: str = "https://api.europeana.eu/record/v2/search.json"
    europeana_api_key: str = ""

    # Runtime capability probing
    enable_capability_probing: bool = True
    capability_probe_use_fixtures: bool = True
    capability_probe_timeout_seconds: float = Field(default=3.0, gt=0)
    capability_probe_cache_ttl_seconds: int = Field(default=300, ge=0)

    model_config = SettingsConfigDict(env_prefix="CLAFOUTIS_", extra="ignore")


settings = Settings()
