import socket
from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect, text
from sqlalchemy.engine import make_url

from prontuario_backend.config.auth import hash_password, issue_access_token
from prontuario_backend.config.database import engine, engine_for
from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app
from prontuario_backend.models.users import bootstrap_system_admin
from prontuario_backend.views.errors import ErrorResponse

SIGNING_SECRET = "isolated-f01-database-signing-key-with-at-least-32-bytes"
PASSWORD = "Isolated-endpoint-password-123"


@pytest.fixture(scope="module")
def password_hash():
    return hash_password(PASSWORD)


@pytest.fixture
def principal(application_schema, password_hash, monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", SIGNING_SECRET)
    get_settings.cache_clear()
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject, password_hash)
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "password",
                "username": "admin",
                "password": PASSWORD,
                "scope": "identity:read",
            },
        )
        assert response.status_code == 200
        credentials = response.json()
    with application_schema.connect() as connection:
        session_id = connection.scalar(text("SELECT id FROM cadastro__sessoes_usuario"))
    return application_schema, subject, session_id, credentials["access_token"]


@contextmanager
def refused_sql_connection(mysql_url, monkeypatch):
    # Porta reservada, sem listen: recusa TCP real, sem parar o MySQL ou disputar porta livre.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        unavailable = make_url(mysql_url).set(
            host="127.0.0.1", port=reserved.getsockname()[1]
        )
        try:
            with monkeypatch.context() as outage:
                outage.setenv(
                    "DATABASE_URL", unavailable.render_as_string(hide_password=False)
                )
                get_settings.cache_clear()
                engine_for.cache_clear()
                yield
        finally:
            get_settings.cache_clear()
            engine_for.cache_clear()


def test_health_is_public_and_queries_only_sql_health_without_creating_tables(
    mysql_url,
):
    database = engine()
    tables = inspect(database).get_table_names()
    statements = []

    def observe(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.strip().upper())

    event.listen(database, "before_cursor_execute", observe)
    try:
        with TestClient(create_app(), base_url="http://localhost") as client:
            response = client.get(
                "/health", headers={"Authorization": "Bearer malformed"}
            )
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok"}
        assert statements == ["SELECT 1"]
    finally:
        event.remove(database, "before_cursor_execute", observe)
    assert inspect(database).get_table_names() == tables
    assert database.pool.checkedout() == 0


def test_identity_with_real_login_returns_only_its_subject_and_executes_only_reads(
    principal, caplog
):
    database, subject, _, token = principal
    statements = []

    def observe(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().split()[0].upper())

    event.listen(database, "before_cursor_execute", observe)
    try:
        with TestClient(create_app(), base_url="http://localhost") as client:
            response = client.get(
                "/api/v1/me", headers={"Authorization": "Bearer " + token}
            )
        assert response.status_code == 200
        assert response.json() == {"subject": subject}
        assert statements and set(statements) == {"SELECT"}
    finally:
        event.remove(database, "before_cursor_execute", observe)
    for private in (token, PASSWORD, SIGNING_SECRET):
        assert private not in response.text + caplog.text
    assert database.pool.checkedout() == 0


@pytest.mark.parametrize("mismatch", ["subject", "session"])
def test_valid_signature_cannot_use_another_or_missing_session(principal, mismatch):
    _, subject, session_id, _ = principal
    token, _ = issue_access_token(
        str(uuid4()) if mismatch == "subject" else subject,
        str(uuid4()) if mismatch == "session" else session_id,
        frozenset({"identity:read"}),
    )
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token}
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "http_401"


def test_valid_session_without_required_scope_is_forbidden(principal):
    _, subject, session_id, _ = principal
    token, _ = issue_access_token(subject, session_id, frozenset())
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token}
        )
    assert response.status_code == 403
    assert (
        response.headers["www-authenticate"]
        == 'Bearer error="insufficient_scope", scope="identity:read"'
    )


def test_sql_refusal_blocks_valid_identity_and_health_then_recovers(
    principal, mysql_url, monkeypatch, caplog
):
    _, subject, _, token = principal
    headers = {"Authorization": "Bearer " + token}
    with TestClient(create_app(), base_url="http://localhost") as client:
        with refused_sql_connection(mysql_url, monkeypatch):
            for path in ("/health", "/api/v1/me"):
                response = client.get(path, headers=headers)
                assert response.status_code == 503
                body = ErrorResponse.model_validate(response.json())
                assert body.error.code == "http_503"
                assert str(body.error.request_id) == response.headers["x-request-id"]
                assert response.headers["cache-control"] == "no-store"
                for private in (
                    token,
                    SIGNING_SECRET,
                    "test-only-password",
                    "mysql+pymysql",
                    "pymysql.err",
                    "Traceback",
                ):
                    assert private not in response.text + caplog.text
            assert client.get("/api/v1/me").status_code == 401
            assert (
                client.get(
                    "/api/v1/me", headers={"Authorization": "Bearer malformed"}
                ).status_code
                == 401
            )
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/me", headers=headers).json() == {"subject": subject}
