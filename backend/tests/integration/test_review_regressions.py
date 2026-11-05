from pathlib import Path
from uuid import uuid4

import certifi
import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import select
from tests.safety import validate_test_database

from prontuario_backend.config.database import session
from prontuario_backend.config.settings import Settings, get_settings
from prontuario_backend.controllers.permissions import require_record_access
from prontuario_backend.main import create_app
from prontuario_backend.models.security import AuditEvent, RecordPermission


def production_settings(**changes):
    values = dict(app_env="production", database_url="mysql+pymysql://unused@localhost/review",
                  mysql_ssl_ca=certifi.where(), redis_url="rediss://localhost:6379/0",
                  oidc_issuer="https://identity.example.test", oidc_audience="review",
                  oidc_jwks_url="https://identity.example.test/jwks",
                  oidc_authorization_url="https://identity.example.test/authorize",
                  oidc_token_url="https://identity.example.test/token", _env_file=None)
    return Settings(**(values | changes))


@pytest.mark.parametrize("changes", [
    {"mysql_ssl_ca": ""}, {"mysql_ssl_ca": "/nonexistent/ca.pem"},
    {"redis_url": "redis://localhost:6379/0"},
    {"redis_url": "rediss://localhost:6379/0?ssl_cert_reqs=none"},
    {"database_url": "mysql+pymysql://unused@localhost/review?ssl_disabled=true"},
    {"redis_url": "rediss://localhost:6379/0?socket_timeout=0"},
    {"redis_connect_timeout": 0}, {"redis_socket_timeout": -1},
])
def test_production_rejects_insecure_transport(changes):
    with pytest.raises(ValidationError):
        production_settings(**changes)


def test_production_accepts_verified_tls():
    assert production_settings().app_env == "production"


def test_framework_errors_follow_contract():
    with TestClient(create_app(), base_url="http://localhost") as client:
        for method, path, status in [("GET", "/missing", 404), ("POST", "/health", 405), ("GET", "/api/v1/me", 401)]:
            response = client.request(method, path)
            assert response.status_code == status
            assert response.json()["error"]["code"] == f"http_{status}"
            assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
            if status == 405:
                assert "GET" in response.headers["Allow"]
            if status == 401:
                assert response.headers["WWW-Authenticate"] == "Bearer"


def test_redis_timeouts_fail_closed(monkeypatch):
    from prontuario_backend.config import http
    options = {}

    class BrokenRedis:
        async def eval(self, *args):
            raise RedisTimeoutError("Simulated stalled service")

    def factory(url, **kwargs):
        options.update(kwargs)
        return BrokenRedis()

    monkeypatch.setenv("REDIS_URL", "rediss://localhost:6379/0")
    monkeypatch.setattr(http.Redis, "from_url", factory)
    get_settings.cache_clear()
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "temporarily_unavailable"
    assert options["socket_connect_timeout"] == 2
    assert options["socket_timeout"] == 2
    assert options["ssl_cert_reqs"] == "required"
    assert options["ssl_check_hostname"] is True
    assert options["retry"].get_retries() == 0


@pytest.mark.parametrize("url, application_urls, confirmation", [
    ("mysql+pymysql://test@localhost/prontuario_test", [], None),
    ("mysql+pymysql://test@localhost/prontuario_test", [], "wrong"),
    ("mysql+pymysql://test@localhost/prontuario_production", [], "prontuario_production"),
    ("mysql+pymysql://test@localhost/prontuario_test", ["mysql+pymysql://app@127.0.0.1/prontuario_test"], "prontuario_test"),
    ("mysql+pymysql://test@localhost/prontuario_test", ["mysql+pymysql://app@localhost:3306/PRONTUARIO_TEST"], "prontuario_test"),
])
def test_cleanup_guard_rejects_unsafe_targets(url, application_urls, confirmation):
    with pytest.raises(ValueError):
        validate_test_database(url, application_urls, confirmation)


def test_cleanup_guard_accepts_separate_explicit_database():
    validate_test_database("mysql+pymysql://test@localhost/prontuario_test", ["mysql+pymysql://app@localhost/prontuario"], "prontuario_test")


def test_subjects_preserve_trailing_spaces_and_case(mysql_url):
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(cfg, "head")
    subject, record, request = "subject-" + uuid4().hex, str(uuid4()), str(uuid4())
    with session() as db:
        db.add(RecordPermission(subject=subject, record_id=record, action="read"))
        db.commit()
    require_record_access(subject, record, "read", request)
    for different_subject in (subject + " ", subject.upper()):
        with pytest.raises(HTTPException) as error:
            require_record_access(different_subject, record, "read", request)
        assert error.value.status_code == 403
    with session() as db:
        db.add(RecordPermission(subject=subject + " ", record_id=record, action="read"))
        db.commit()
    require_record_access(subject + " ", record, "read", request)
    with session() as db:
        assert len(db.scalars(select(RecordPermission)).all()) == 2
        assert len(db.scalars(select(AuditEvent)).all()) == 4
