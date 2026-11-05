import jwt
from fastapi.testclient import TestClient
from prontuario_backend.main import app

client = TestClient(app)


def test_health_uses_sql(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert (tmp_path / "test.db").exists()


def test_protected_route_requires_token():
    assert client.get("/api/v1/me").status_code == 401


def test_provider_not_configured_fails_closed(monkeypatch):
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer example"})
    assert response.status_code == 503


def test_openapi_and_swagger():
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["OAuth2AuthorizationCodeBearer"]["flows"]["authorizationCode"]
    assert schema["paths"]["/api/v1/me"]["get"]["security"]
    assert client.get("/docs").status_code == 200


def test_signed_token_and_rejections(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from cryptography.hazmat.primitives.asymmetric import rsa
    from prontuario_backend.config import auth

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example.test")
    monkeypatch.setenv("OIDC_AUDIENCE", "prontuario-test")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example.test/jwks")
    monkeypatch.setattr(auth, "jwks_client", lambda url: SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key=private_key.public_key())
    ))
    claims = {"iss": "https://issuer.example.test", "aud": "prontuario-test",
              "sub": "synthetic-user", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}

    def request(payload):
        token = jwt.encode(payload, private_key, algorithm="RS256")
        return client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert request(claims).json() == {"subject": "synthetic-user"}
    assert request({**claims, "aud": "other-api"}).status_code == 401
    assert request({**claims, "exp": datetime.now(timezone.utc) - timedelta(seconds=5)}).status_code == 401
