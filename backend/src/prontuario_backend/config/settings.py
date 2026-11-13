from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
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
    auth_jwt_secret: SecretStr | None = None
    auth_jwt_issuer: str = "prontuarioedu"
    auth_jwt_audience: str = "prontuario-api"
    auth_access_token_minutes: int = Field(default=15, ge=1, le=60)
    auth_refresh_token_days: int = Field(default=7, ge=1, le=30)
    auth_refresh_window_seconds: int = Field(default=60, ge=0, le=3600)

    @model_validator(mode="after")
    def validate_environment(self):
        if self.max_body_bytes < 1 or self.rate_limit < 1:
            raise ValueError("Limits must be positive")
        if not self.allowed_hosts or "*" in self.allowed_hosts or "*" in self.cors_origins:
            raise ValueError("Explicit hosts and origins required")
        if self.auth_jwt_secret and len(self.auth_jwt_secret.get_secret_value().encode()) < 32:
            raise ValueError("JWT signing secret requires at least 32 bytes")
        if not self.auth_jwt_issuer or not self.auth_jwt_audience:
            raise ValueError("JWT issuer and audience are required")
        try:
            database = make_url(self.database_url.get_secret_value())
        except (ArgumentError, ValueError):
            raise ValueError("Invalid MySQL connection URL") from None
        if database.drivername != "mysql+pymysql":
            raise ValueError("MySQL with PyMySQL is required")
        if not database.host or not database.host.strip() or not database.database or not database.database.strip():
            raise ValueError("MySQL requires an explicit server and database name")
        if database.port is not None and not 1 <= database.port <= 65535:
            raise ValueError("Invalid MySQL server port")
        if any(key.lower().startswith("ssl") or key.lower() in {"connect_timeout", "read_timeout", "write_timeout"} for key in database.query):
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
            if not self.redis_url or not self.auth_jwt_secret:
                raise ValueError("Production requires Redis and a JWT signing secret")
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
