from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select

from prontuario_backend.config.database import session
from prontuario_backend.config.settings import Settings, get_settings
from prontuario_backend.controllers.permissions import require_record_access
from prontuario_backend.main import create_app
from prontuario_backend.models.security import AuditEvent, RecordPermission


def test_production_rejects_incomplete_configuration():
    with pytest.raises(ValidationError):
        Settings(app_env="production", _env_file=None)


def test_headers_limits_and_logs(monkeypatch, caplog):
    monkeypatch.setenv("RATE_LIMIT", "1")
    monkeypatch.setenv("MAX_BODY_BYTES", "16")
    get_settings.cache_clear()
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me?token=DO_NOT_LOG")
        assert response.status_code == 401
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-request-id"]
        assert client.get("/api/v1/me").status_code == 429
        assert client.post("/health", content="x" * 17).status_code == 413
        assert client.get("/health", headers={"host": "unexpected.example"}).status_code == 400
        preflight = client.options("/health", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in preflight.headers
        assert client.get("/metrics").status_code == 200
    assert "DO_NOT_LOG" not in caplog.text


def test_migrations_empty_database_and_deny_by_default(mysql_url):
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
    with session() as db:
        assert db.scalar(select(func.count()).select_from(RecordPermission)) == 0
        assert db.scalar(select(func.count()).select_from(AuditEvent)) == 0
    # Isolated test identities are never inserted into the application database.
    subject, record, request = str(uuid4()), str(uuid4()), str(uuid4())
    with pytest.raises(HTTPException) as error:
        require_record_access(subject, record, "read", request)
    assert error.value.status_code == 403
    with session() as db:
        assert db.scalar(select(AuditEvent.outcome)) == "denied"
        db.add(RecordPermission(subject=subject, record_id=record, action="read"))
        db.commit()
    require_record_access(subject, record, "read", request)
    with pytest.raises(HTTPException):
        require_record_access(subject, str(uuid4()), "read", request)
    with pytest.raises(HTTPException):
        require_record_access(subject, record, "write", request)
    with session() as db:
        assert db.scalar(select(func.count()).select_from(AuditEvent)) == 4


def test_production_hides_docs_and_metrics(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://unused@localhost/unused")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    for key in ("OIDC_ISSUER", "OIDC_JWKS_URL", "OIDC_AUTHORIZATION_URL", "OIDC_TOKEN_URL"):
        monkeypatch.setenv(key, "https://identity.example.test/endpoint")
    monkeypatch.setenv("OIDC_AUDIENCE", "test-only")
    get_settings.cache_clear()
    with TestClient(create_app(), base_url="http://localhost") as client:
        for path in ("/docs", "/openapi.json", "/metrics"):
            response = client.get(path)
            assert response.status_code == 404
            assert response.headers["strict-transport-security"] == "max-age=31536000"
