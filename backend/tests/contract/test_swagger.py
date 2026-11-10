from fastapi.testclient import TestClient

from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app


def test_swagger_uses_forwarded_origin_for_api_and_oauth_callback(monkeypatch):
    host = "swagger-contract-8000.app.github.dev"
    monkeypatch.setenv("ALLOWED_HOSTS", f'["localhost","{host}"]')
    monkeypatch.setenv("SWAGGER_CLIENT_ID", "swagger-contract-client")
    get_settings.cache_clear()
    with TestClient(create_app(), base_url=f"https://{host}") as client:
        response = client.get("/docs")
        assert response.status_code == 200
        assert '"clientId": "swagger-contract-client"' in response.text
        assert '"usePkceWithAuthorizationCodeGrant": true' in response.text
        assert '"persistAuthorization": false' in response.text
        assert "window.location.origin + '/docs/oauth2-redirect'" in response.text
        assert "clientSecret" not in response.text
        assert client.get("/docs/oauth2-redirect").status_code == 200
        schema = client.get("/openapi.json").json()
        assert schema["servers"][0]["url"] == "/"
        identity = schema["paths"]["/api/v1/me"]["get"]
        assert identity["operationId"] == "get_current_identity"
        assert identity["security"] == [{"OAuth2AuthorizationCodeBearer": []}]
        assert "401" in identity["responses"]
        assert "security" not in schema["paths"]["/health"]["get"]
        # Loading documentation does not authenticate a user or connect to MySQL.
        assert client.get("/api/v1/me").status_code == 401


def test_swagger_without_client_configuration_still_loads(monkeypatch):
    monkeypatch.setenv("SWAGGER_CLIENT_ID", "")
    get_settings.cache_clear()
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/docs")
        assert response.status_code == 200
        assert '"clientId"' not in response.text
        assert client.get("/openapi.json").status_code == 200
