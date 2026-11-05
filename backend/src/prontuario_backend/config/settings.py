from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr("sqlite:///./data/development.db")
    redis_url: SecretStr | None = None
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    cors_origins: list[str] = []
    max_body_bytes: int = 1048576
    rate_limit: int = 120
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    oidc_authorization_url: str = ""
    oidc_token_url: str = ""

    @model_validator(mode="after")
    def validate_environment(self):
        if self.max_body_bytes < 1 or self.rate_limit < 1:
            raise ValueError("Limits must be positive")
        if not self.allowed_hosts or "*" in self.allowed_hosts or "*" in self.cors_origins:
            raise ValueError("Explicit hosts and origins required")
        for url in (self.oidc_issuer, self.oidc_jwks_url, self.oidc_authorization_url, self.oidc_token_url):
            if url and (urlsplit(url).scheme != "https" or not urlsplit(url).hostname):
                raise ValueError("OIDC requires HTTPS")
        if self.app_env == "production":
            if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
                raise ValueError("Production requires PostgreSQL")
            if not self.redis_url or not all((self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url, self.oidc_authorization_url, self.oidc_token_url)):
                raise ValueError("Production requires Redis and OIDC")
            if any(not origin.startswith("https://") for origin in self.cors_origins):
                raise ValueError("Production origins require HTTPS")
        return self


@lru_cache
def get_settings():
    try:
        return Settings()
    except ValidationError:
        # Do not expose connection strings or other input values in startup errors.
        raise RuntimeError("Configuração inválida; confira as variáveis do ambiente") from None
