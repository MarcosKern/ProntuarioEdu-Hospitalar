import os

from dotenv import dotenv_values

APPLICATION_DATABASE_URLS = (os.getenv("DATABASE_URL"), dotenv_values(".env").get("DATABASE_URL"))

# Collection must not open a real application connection. Never print configured URLs.
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://unused@127.0.0.1/prontuario_test")

import pytest
from sqlalchemy import create_engine, text

from prontuario_backend.config.database import engine_for
from prontuario_backend.config.settings import get_settings
from tests.safety import validate_test_database


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    url = os.getenv("MYSQL_TEST_URL")
    if url:
        validate_test_database(url, APPLICATION_DATABASE_URLS, os.getenv("MYSQL_TEST_ALLOW_RESET"))
        admin = create_engine(url)
        with admin.begin() as connection:
            # Only reset the explicitly designated disposable test database.
            for table in ("audit_events", "record_permissions", "alembic_version"):
                connection.execute(text(f"DROP TABLE IF EXISTS {table}"))
        admin.dispose()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", url or "mysql+pymysql://unused@127.0.0.1/prontuario_test")
    monkeypatch.delenv("REDIS_URL", raising=False)
    for name in ("OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL", "OIDC_AUTHORIZATION_URL", "OIDC_TOKEN_URL"):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    engine_for.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mysql_url():
    url = os.getenv("MYSQL_TEST_URL")
    if not url:
        pytest.skip("MYSQL_TEST_URL is required for database integration tests")
    return url
