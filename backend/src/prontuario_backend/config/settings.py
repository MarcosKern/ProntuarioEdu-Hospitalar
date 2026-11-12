from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr
    mysql_ssl_ca: str = ""
    mysql_connect_timeout: int = Field(default=5, gt=0, le=120)
    mysql_read_timeout: float = Field(default=10, gt=0, le=120)
    mysql_write_timeout: float = Field(default=10, gt=0, le=120)
    mysql_pool_timeout: float = Field(default=5, gt=0, le=120)
    redis_url: SecretStr | None = None
    redis_ssl_ca: str = ""
    redis_connect_timeout: float = Field(default=2, gt=0, le=30)
    redis_socket_timeout: float = Field(default=2, gt=0, le=30)
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    cors_origins: list[str] = []
    max_body_bytes: int = 1048576
    rate_limit: int = 120
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    oidc_authorization_url: str = ""
    oidc_token_url: str = ""
    oidc_scope_claim: Literal["scope", "scp"] = "scope"
    oidc_refresh_window_seconds: int = Field(default=60, ge=0, le=3600)
    swagger_client_id: str = ""

    @model_validator(mode="after")
    def validate_environment(self):
        if self.max_body_bytes < 1 or self.rate_limit < 1:
            raise ValueError("Limits must be positive")
        if not self.allowed_hosts or "*" in self.allowed_hosts or "*" in self.cors_origins:
            raise ValueError("Explicit hosts and origins required")
        for url in (self.oidc_issuer, self.oidc_jwks_url, self.oidc_authorization_url, self.oidc_token_url):
            if url and (urlsplit(url).scheme != "https" or not urlsplit(url).hostname):
                raise ValueError("OIDC requires HTTPS")
        if not self.database_url.get_secret_value().startswith("mysql+pymysql://"):
            raise ValueError("MySQL with PyMySQL is required")
        db_query = parse_qs(urlsplit(self.database_url.get_secret_value()).query)
        if any(key.lower().startswith("ssl") or key.lower() in {"connect_timeout", "read_timeout", "write_timeout"} for key in db_query):
            raise ValueError("Configure MySQL TLS and timeouts through settings")
        for ca in (self.mysql_ssl_ca, self.redis_ssl_ca):
            if ca and not Path(ca).is_file():
                raise ValueError("Configured CA must be a readable file")
        if self.redis_url:
            redis = urlsplit(self.redis_url.get_secret_value())
            if redis.scheme not in {"redis", "rediss"} or not redis.hostname:
                raise ValueError("Invalid Redis URL")
            reserved = {"ssl_cert_reqs", "ssl_check_hostname", "socket_timeout", "socket_connect_timeout", "retry_on_timeout"}
            if reserved.intersection(key.lower() for key in parse_qs(redis.query)):
                raise ValueError("Configure Redis TLS and timeouts through settings")
        if self.app_env == "production":
            if not self.mysql_ssl_ca:
                raise ValueError("Production MySQL requires a trusted CA")
            if self.redis_url and urlsplit(self.redis_url.get_secret_value()).scheme != "rediss":
                raise ValueError("Production Redis requires TLS")
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
