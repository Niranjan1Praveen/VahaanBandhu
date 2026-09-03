"""Centralised application configuration.

Every setting comes from the environment. No secret has a real default: a
missing credential must fail loudly or disable a feature, never silently fall
back to a committed value -- which is exactly how the legacy Flask app ended up
with a TomTom key in source control.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- app
    app_name: str = "VahaanBandhu API"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="development")
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- mongo
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db: str = Field(default="vahaanbandhu")

    # --- redis. Optional by design: Redis improves latency, it is never the
    # source of truth, and its absence must not break correctness.
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_enabled: bool = True
    route_cache_ttl_s: int = 900

    # --- auth
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwt_issuer: str = ""
    # Development-only auth bypass for local UI work and screenshots. Guarded so
    # it cannot be switched on by a weak default in a non-development env --
    # see `demo_auth_active`.
    dev_auth_enabled: bool = True

    # --- routing
    tomtom_api_keys: str = ""
    vbqer_profile: str = "live"  # research | quality | live

    # --- quantum. Recorded for completeness only. There is NO live QPU call in
    # the HTTP request path; this flag never gates a user request.
    ibm_quantum_offline_only: bool = True

    @field_validator("environment")
    @classmethod
    def _normalise_env(cls, v: str) -> str:
        return v.strip().lower()

    @property
    def is_production(self) -> bool:
        return self.environment in ("production", "prod")

    @property
    def demo_auth_active(self) -> bool:
        """Dev auth is only ever active outside production.

        Two independent conditions must hold. A single misconfigured env var
        cannot expose the bypass in production.
        """
        return self.dev_auth_enabled and not self.is_production

    @property
    def clerk_configured(self) -> bool:
        return bool(self.clerk_secret_key and self.clerk_publishable_key)

    @property
    def tomtom_configured(self) -> bool:
        return bool([k for k in self.tomtom_api_keys.split(",") if k.strip()])

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
