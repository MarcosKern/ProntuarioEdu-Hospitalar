from fastapi.testclient import TestClient

from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app


def test_swagger_login_uses_api_origin_in_codespaces(monkeypatch):
    host = "swagger-contract-8000.app.github.dev"
    monkeypatch.setenv("ALLOWED_HOSTS", f'["localhost","{host}"]')
    get_settings.cache_clear()
    with TestClient(create_app(), base_url=f"https://{host}") as client:
        response = client.get("/docs")
        assert response.status_code == 200
        assert '"persistAuthorization": false' in response.text
        assert "usePkceWithAuthorizationCodeGrant" not in response.text
        assert "clientSecret" not in response.text
        assert client.get("/docs/oauth2-redirect").status_code == 404
        schema = client.get("/openapi.json").json()
        assert schema["servers"][0]["url"] == "/"
        flow = schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]
        assert set(flow) == {"password"}
        assert flow["password"]["tokenUrl"] == "/api/v1/auth/token"
        identity = schema["paths"]["/api/v1/me"]["get"]
        assert identity["security"] == [
            {"OAuth2PasswordBearer": ["identity:read"]},
            {"BearerToken": []},
        ]
        assert "security" not in schema["paths"]["/health"]["get"]
        assert client.get("/api/v1/me").status_code == 401
        assert (
            client.get("/docs", headers={"host": "untrusted.example"}).status_code
            == 400
        )
        token = schema["paths"]["/api/v1/auth/token"]["post"]
        fields = token["requestBody"]["content"]["application/x-www-form-urlencoded"][
            "schema"
        ]
        assert fields["properties"]["password"]["format"] == "password"


def test_manual_bearer_is_an_alternative_only_for_protected_routes():
    app = create_app()
    schema = app.openapi()
    assert schema["components"]["securitySchemes"]["BearerToken"]["scheme"] == "bearer"
    assert "security" not in schema["paths"]["/health"]["get"]
    assert "security" not in schema["paths"]["/api/v1/auth/token"]["post"]
    assert app.openapi() == schema
    assert (
        schema["paths"]["/api/v1/me"]["get"]["security"].count({"BearerToken": []}) == 1
    )
