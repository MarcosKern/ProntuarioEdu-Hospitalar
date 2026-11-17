from fastapi.testclient import TestClient

from prontuario_backend.main import app

client = TestClient(app, base_url="http://localhost")


def test_health_uses_sql(mysql_url):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_protected_route_requires_token():
    assert client.get("/api/v1/me").status_code == 401


def test_signing_not_configured_fails_closed():
    assert (
        client.get(
            "/api/v1/me", headers={"Authorization": "Bearer example"}
        ).status_code
        == 503
    )


def test_openapi_and_swagger():
    schema = client.get("/openapi.json").json()
    assert (
        schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"][
            "password"
        ]["tokenUrl"]
        == "/api/v1/auth/token"
    )
    assert schema["paths"]["/api/v1/me"]["get"]["security"]
    assert client.get("/docs").status_code == 200
