import os

# Collection must not require a real application connection or read a developer secret.
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://unused@127.0.0.1/prontuario_test")

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from prontuario_backend.config.database import engine_for
from prontuario_backend.config.settings import get_settings


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    url = os.getenv("MYSQL_TEST_URL")
    if url:
        assert make_url(url).database.startswith("prontuario_test"), "A dedicated test database is required"
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
