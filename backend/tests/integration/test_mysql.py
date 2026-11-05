import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from prontuario_backend.config.database import engine
from prontuario_backend.config.settings import get_settings


def test_mysql_migrations_and_audit_protection(monkeypatch):
    url = os.getenv("MYSQL_TEST_URL")
    if not url:
        pytest.skip("MYSQL_TEST_URL not set; run CI or the MySQL integration command")
    assert make_url(url).database.startswith("prontuario_test"), "Use a dedicated test database"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
    # A transaction-local test row is rolled back and never retained.
    with engine().connect() as db:
        tx = db.begin()
        db.execute(text("INSERT INTO audit_events VALUES ('test', CURRENT_TIMESTAMP, 'test', 'test', 'read', 'denied', 'test')"))
        with pytest.raises(DBAPIError):
            db.execute(text("DELETE FROM audit_events WHERE id='test'"))
        tx.rollback()
