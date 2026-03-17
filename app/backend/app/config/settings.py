"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend application."""

    app_name: str = "Clafoutis Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, gt=0)
    request_timeout_seconds: float = Field(default=8.0, gt=0)
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    serve_frontend: bool = True
    frontend_dist_dir: str = "app/frontend/dist"

    gallica_sru_base_url: str = "https://gallica.bnf.fr/SRU"
    gallica_use_fixtures: bool = True
    bodleian_api_base_url: str = "https://digital.bodleian.ox.ac.uk"
    bodleian_use_fixtures: bool = True
    europeana_api_base_url: str = "https://api.europeana.eu/record/v2/search.json"
    europeana_api_key: str | None = None
    europeana_use_fixtures: bool = True

    enable_capability_probing: bool = True
    capability_probe_timeout_seconds: float = Field(default=2.0, gt=0)
    capability_probe_cache_ttl_seconds: int = Field(default=300, ge=0)
    capability_probe_use_fixtures: bool = True

    model_config = SettingsConfigDict(env_prefix="CLAFOUTIS_", extra="ignore")


settings = Settings()
