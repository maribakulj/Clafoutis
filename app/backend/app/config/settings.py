"""Application settings loaded from environment variables."""

from __future__ import annotations

import re

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_TRUTHY_TOKENS = {"1", "true", "yes", "on", "enable", "enabled"}
_FALSY_TOKENS = {"0", "false", "no", "off", "disable", "disabled"}


def _parse_bool_with_fallback(value: object, default: bool) -> bool:
    """Parse permissive boolean-like values and fall back to default when ambiguous."""

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if not isinstance(value, str):
        return default

    normalized = value.strip().lower()
    if normalized in _TRUTHY_TOKENS:
        return True
    if normalized in _FALSY_TOKENS:
        return False

    tokens = re.findall(r"[a-z0-9]+", normalized)
    has_truthy = any(token in _TRUTHY_TOKENS for token in tokens)
    has_falsy = any(token in _FALSY_TOKENS for token in tokens)

    if has_truthy and not has_falsy:
        return True
    if has_falsy and not has_truthy:
        return False

    return default


class Settings(BaseSettings):
    """Runtime settings for the backend application."""

    app_name: str = "Clafoutis Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    request_timeout_seconds: float = Field(default=8.0, gt=0)
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    serve_frontend: bool = True
    frontend_dist_dir: str = "app/frontend/dist"

    # Connector settings (fixture-first for MVP demo stability)
    gallica_use_fixtures: bool = True
    gallica_sru_base_url: str = "https://gallica.bnf.fr/SRU"
    bodleian_use_fixtures: bool = True
    bodleian_api_base_url: str = "https://api.bodleian.ox.ac.uk/iiif"
    europeana_use_fixtures: bool = True
    europeana_api_base_url: str = "https://api.europeana.eu/record/v2/search.json"
    europeana_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("CLAFOUTIS_EUROPEANA_API_KEY", "EUROPEANA_API_KEY", "HF_TOKEN"),
    )

    # Runtime capability probing
    enable_capability_probing: bool = True
    capability_probe_use_fixtures: bool = True
    capability_probe_timeout_seconds: float = Field(default=3.0, gt=0)
    capability_probe_cache_ttl_seconds: int = Field(default=300, ge=0)

    @field_validator(
        "debug",
        "serve_frontend",
        "gallica_use_fixtures",
        "bodleian_use_fixtures",
        "europeana_use_fixtures",
        "enable_capability_probing",
        "capability_probe_use_fixtures",
        mode="before",
    )
    @classmethod
    def normalize_bool_env_values(cls, value: object, info):
        """Normalize permissive boolean-like environment values for robust deployments."""

        default = bool(cls.model_fields[info.field_name].default)
        return _parse_bool_with_fallback(value=value, default=default)

    model_config = SettingsConfigDict(env_prefix="CLAFOUTIS_", extra="ignore")


settings = Settings()
