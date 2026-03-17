"""Application settings loaded from environment variables."""

import re

from pydantic import AliasChoices, Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend application."""

    app_name: str = "Clafoutis Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    request_timeout_seconds: float = Field(default=8.0, gt=0)
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    serve_frontend: str | bool = True
    frontend_dist_dir: str = "app/frontend/dist"

    # Connector settings
    gallica_use_fixtures: bool = False
    gallica_sru_base_url: str = "https://gallica.bnf.fr/SRU"
    bodleian_use_fixtures: bool = False
    bodleian_api_base_url: str = "https://api.bodleian.ox.ac.uk/iiif"
    europeana_use_fixtures: bool = False
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

    @staticmethod
    def _coerce_bool_field(field_name: str, value: object, default: bool) -> object:
        """Best-effort coercion for boolean env values used in hosted platforms."""

        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if not isinstance(value, str):
            return value

        normalized = value.strip().lower()
        truthy = {"1", "true", "yes", "on"}
        falsy = {"0", "false", "no", "off", ""}

        if normalized in truthy:
            return True
        if normalized in falsy:
            return False

        first_token = re.split(r"[^a-z0-9]+", normalized, maxsplit=1)[0]
        if first_token in truthy:
            return True
        if first_token in falsy:
            return False

        if field_name.endswith("_use_fixtures") and "fixture" in normalized:
            return True
        if field_name == "serve_frontend" and "frontend" in normalized:
            return True

        return default

    @property
    def serve_frontend_enabled(self) -> bool:
        """Resolved frontend serving flag tolerant to descriptive env values."""

        return bool(self._coerce_bool_field("serve_frontend", self.serve_frontend, True))

    @model_validator(mode="before")
    @classmethod
    def normalize_boolean_fields(cls, values: object) -> object:
        """Normalize raw settings payload before strict bool parsing."""

        if not isinstance(values, dict):
            return values

        bool_fields = {
            "debug",
            "serve_frontend",
            "gallica_use_fixtures",
            "bodleian_use_fixtures",
            "europeana_use_fixtures",
            "enable_capability_probing",
            "capability_probe_use_fixtures",
        }
        normalized_values = dict(values)
        for field_name in bool_fields:
            if field_name not in normalized_values:
                continue
            default = bool(cls.model_fields[field_name].default)
            normalized_values[field_name] = cls._coerce_bool_field(
                field_name=field_name,
                value=normalized_values[field_name],
                default=default,
            )

        return normalized_values

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

        return cls._coerce_bool_field(
            field_name=info.field_name,
            value=value,
            default=bool(cls.model_fields[info.field_name].default),
        )

    model_config = SettingsConfigDict(env_prefix="CLAFOUTIS_", extra="ignore")


settings = Settings()
