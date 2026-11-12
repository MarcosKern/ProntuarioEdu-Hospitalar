import os
import re
from pathlib import Path

from dotenv import dotenv_values

APPLICATION_DATABASE_URLS = (os.getenv("DATABASE_URL"), dotenv_values(".env").get("DATABASE_URL"))

# Collection must not open a real application connection. Never print configured URLs.
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://unused@127.0.0.1/prontuario_test")

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from prontuario_backend.config.database import engine, engine_for
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
    # Empty process values also override real development values in .env.
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("AUTH_JWT_SECRET", "")
    monkeypatch.setenv("AUTH_JWT_ISSUER", "prontuarioedu")
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", "prontuario-api")
    monkeypatch.setenv("AUTH_REFRESH_WINDOW_SECONDS", "60")
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


TABLES = ['cadastro__unidades', 'cadastro__profissionais', 'cadastro__usuarios', 'cadastro__perfis',
          'cadastro__permissoes', 'cadastro__perfil_permissao', 'cadastro__usuario_perfil', 'cadastro__sessoes_usuario']


@pytest.fixture
def application_schema(mysql_url):
    backend = Path(__file__).resolve().parents[1]
    command.upgrade(Config(str(backend / 'alembic.ini')), 'head')
    source = (backend / 'docs/database/prontuarioedu_mysql.sql').read_text()
    db = engine()
    with db.begin() as connection:
        for table in TABLES:
            ddl = re.search(r'CREATE TABLE `' + table + r'` \(.*?;', source, re.S)
            assert ddl
            connection.execute(text(ddl.group()))
        for match in re.finditer(r'ALTER TABLE `([^`]+)`[^;]+;', source):
            if match[1] in TABLES:
                connection.execute(text(match.group()))
        for match in re.finditer(r'CREATE UNIQUE INDEX [^;]+ ON `([^`]+)`[^;]+;', source):
            if match[1] in TABLES:
                connection.execute(text(match.group()))
    try:
        yield db
    finally:
        with db.begin() as connection:
            for table in reversed(TABLES):
                connection.execute(text('DROP TABLE ' + table))
