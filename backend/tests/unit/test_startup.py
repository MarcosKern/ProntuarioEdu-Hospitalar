from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from prontuario_backend.main import create_app
from prontuario_backend.models import users


def test_startup_and_documentation_do_not_connect_or_create_an_admin(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Startup não pode conectar ou criar cadastros")

    monkeypatch.setattr(Engine, "connect", forbidden)
    monkeypatch.setattr(users, "bootstrap_system_admin", forbidden)
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/api/v1/me").status_code == 401
    assert calls == []
