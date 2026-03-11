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
    gallica_sru_base_url: str = "https://gallica.bnf.fr/SRU"
    gallica_use_fixtures: bool = True

    model_config = SettingsConfigDict(env_prefix="CLAFOUTIS_", extra="ignore")


settings = Settings()
