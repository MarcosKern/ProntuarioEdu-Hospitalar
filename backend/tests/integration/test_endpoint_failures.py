import socket
import threading
import time
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from prontuario_backend.config.auth import issue_access_token
from prontuario_backend.config.database import engine, engine_for
from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app
from prontuario_backend.views.errors import ErrorResponse

SIGNING_SECRET = "isolated-f01-endpoint-signing-key-with-at-least-32-bytes"


def assert_error(response, status):
    assert response.status_code == status
    error = ErrorResponse.model_validate(response.json()).error
    assert error.code == f"http_{status}"
    assert str(error.request_id) == response.headers["x-request-id"]
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("kind", ["missing", "basic", "malformed", "expired", "wrong_signature"])
def test_identity_rejects_invalid_credentials_before_any_sql_access(monkeypatch, kind, caplog):
    monkeypatch.setenv("AUTH_JWT_SECRET", SIGNING_SECRET)
    get_settings.cache_clear()
    token, _ = issue_access_token(str(uuid4()), str(uuid4()), frozenset({"identity:read"}))
    if kind in {"expired", "wrong_signature"}:
        claims = jwt.decode(token, SIGNING_SECRET, algorithms=["HS256"], audience="prontuario-api", issuer="prontuarioedu")
        if kind == "expired":
            claims["iat"], claims["exp"] = int(time.time()) - 120, int(time.time()) - 60
        key = SIGNING_SECRET if kind == "expired" else "other-isolated-signing-key-with-at-least-32-bytes"
        token = jwt.encode(claims, key, algorithm="HS256")
    headers = {} if kind == "missing" else {"Authorization": {"basic": "Basic ignored", "malformed": "Bearer malformed"}.get(kind, "Bearer " + token)}
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Credencial inválida não pode consultar SQL")

    monkeypatch.setattr(Engine, "connect", forbidden)
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", params={"access_token": token}, headers=headers)
    assert_error(response, 401)
    assert calls == []
    assert "subject" not in response.json()
    assert token not in response.text + caplog.text
    assert SIGNING_SECRET not in response.text + caplog.text
    assert response.headers["www-authenticate"].startswith("Bearer")


@pytest.mark.parametrize("path", ["/health", "/api/v1/me"])
def test_http_endpoints_bound_a_real_stalled_sql_handshake(monkeypatch, path, caplog):
    stop = threading.Event()
    accepted = threading.Event()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(1)
        port = listener.getsockname()[1]
        monkeypatch.setenv("DATABASE_URL", f"mysql+pymysql://isolated:never-log-this-db-password@127.0.0.1:{port}/prontuario_test")
        monkeypatch.setenv("MYSQL_SSL_CA", "")
        monkeypatch.setenv("MYSQL_READ_TIMEOUT", "0.2")
        monkeypatch.setenv("AUTH_JWT_SECRET", SIGNING_SECRET)
        get_settings.cache_clear()
        engine_for.cache_clear()

        def stalled_server():
            try:
                connection, _ = listener.accept()
                with connection:
                    accepted.set()
                    stop.wait(3)
            except (TimeoutError, OSError):
                pass

        worker = threading.Thread(target=stalled_server, daemon=True)
        worker.start()
        token, _ = issue_access_token(str(uuid4()), str(uuid4()), frozenset({"identity:read"}))
        try:
            with TestClient(create_app(), base_url="http://localhost") as client:
                started = time.monotonic()
                response = client.get(path, headers={"Authorization": "Bearer " + token})
                elapsed = time.monotonic() - started
            assert accepted.is_set()
            assert elapsed < 2
            assert_error(response, 503)
            combined = response.text + caplog.text
            for private in (token, SIGNING_SECRET, "never-log-this-db-password", "pymysql.err", "Traceback"):
                assert private not in combined
            assert engine().pool.checkedout() == 0
        finally:
            stop.set()
            worker.join(timeout=1.5)
            engine().dispose()
            engine_for.cache_clear()
