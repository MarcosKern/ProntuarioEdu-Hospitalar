import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from prontuario_backend.config import database
from prontuario_backend.config.settings import Settings, get_settings
from prontuario_backend.main import create_app
from prontuario_backend.views.errors import ErrorResponse


@pytest.mark.parametrize("field", ["mysql_connect_timeout", "mysql_read_timeout", "mysql_write_timeout", "mysql_pool_timeout"])
@pytest.mark.parametrize("value", [0, -1, 121])
def test_sql_timeouts_must_be_bounded(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="mysql+pymysql://unused@localhost/review", **{field: value})


def test_sql_driver_uses_configured_timeouts(monkeypatch):
    monkeypatch.setenv("MYSQL_CONNECT_TIMEOUT", "3")
    monkeypatch.setenv("MYSQL_READ_TIMEOUT", "4")
    monkeypatch.setenv("MYSQL_WRITE_TIMEOUT", "6")
    monkeypatch.setenv("MYSQL_POOL_TIMEOUT", "2")
    get_settings.cache_clear()
    engine = database.engine_for(get_settings().database_url.get_secret_value())
    observed = {}

    def unavailable(*args, **kwargs):
        observed.update(kwargs)
        raise engine.dialect.dbapi.OperationalError(2013, "isolated connection failure")

    monkeypatch.setattr(engine.dialect, "connect", unavailable)
    with pytest.raises(OperationalError):
        engine.connect()
    assert observed["connect_timeout"] == 3
    assert observed["read_timeout"] == 4
    assert observed["write_timeout"] == 6
    assert engine.pool.timeout() == 2
    engine.dispose()


def test_openapi_matches_error_responses(monkeypatch):
    from prontuario_backend.controllers import health
    monkeypatch.setattr(health, "database_ready", lambda: False)
    with TestClient(create_app(), base_url="http://localhost") as client:
        schema = client.get("/openapi.json").json()
        assert "ErrorResponse" in schema["components"]["schemas"]
        for path, statuses in [("/health", [413, 500, 503]), ("/api/v1/me", [401, 413, 429, 500, 503])]:
            for status in statuses:
                response = schema["paths"][path]["get"]["responses"][str(status)]
                assert response["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")
        for path, status in [("/health", 503), ("/api/v1/me", 401)]:
            response = client.get(path)
            assert response.status_code == status
            parsed = ErrorResponse.model_validate(response.json())
            assert parsed.error.request_id == response.headers["x-request-id"]


def test_internal_error_logs_location_without_sensitive_values(caplog):
    app = create_app()
    secret = "NEVER_LOG_THIS_TOKEN_OR_DATABASE_URL"

    @app.get("/isolated-failure")
    def isolated_failure():
        raise ValueError(secret)

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/isolated-failure")
    assert response.status_code == 500
    assert secret not in response.text
    assert secret not in caplog.text
    diagnostics = [json.loads(r.message) for r in caplog.records if '"event": "unhandled_error"' in r.message]
    assert len(diagnostics) == 1
    assert diagnostics[0]["request_id"] == response.headers["x-request-id"]
    assert diagnostics[0]["error_type"] == "ValueError"
    assert any(frame["function"] == "isolated_failure" for frame in diagnostics[0]["frames"])


def test_mysql_read_timeout_bounds_a_stalled_handshake(monkeypatch):
    import socket
    import threading
    import time

    monkeypatch.setenv("MYSQL_READ_TIMEOUT", "0.2")
    get_settings.cache_clear()
    stop = threading.Event()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(2)
    port = listener.getsockname()[1]

    def silent_server():
        try:
            connection, _ = listener.accept()
            with connection:
                stop.wait(3)
        except TimeoutError:
            pass

    worker = threading.Thread(target=silent_server, daemon=True)
    worker.start()
    engine = database.engine_for(f"mysql+pymysql://unused@127.0.0.1:{port}/isolated_timeout")
    started = time.monotonic()
    try:
        with pytest.raises(OperationalError):
            engine.connect()
        assert time.monotonic() - started < 2
    finally:
        stop.set()
        worker.join(timeout=1)
        listener.close()
        engine.dispose()
