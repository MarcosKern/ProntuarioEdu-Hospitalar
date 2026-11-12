import io
import json
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.error import URLError

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Security
from fastapi.testclient import TestClient
from pydantic import ValidationError

from prontuario_backend.config import auth
from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.config.settings import Settings, get_settings
from prontuario_backend.main import create_app

ISSUER = "https://issuer.example.test"
AUDIENCE = "prontuario-test"
JWKS_URL = ISSUER + "/jwks"
KID = "isolated-test-key"


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def provider(monkeypatch, signing_key):
    monkeypatch.setenv("OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("OIDC_JWKS_URL", JWKS_URL)
    get_settings.cache_clear()
    key = jwt.algorithms.RSAAlgorithm.to_jwk(signing_key.public_key(), as_dict=True)
    state = {"keys": [key | {"kid": KID, "alg": "RS256", "use": "sig"}], "requests": []}

    def open_jwks(opener, request, *, timeout):
        assert request.full_url == JWKS_URL
        assert timeout == 5
        state["requests"].append(request.full_url)
        return io.BytesIO(json.dumps({"keys": state["keys"]}).encode())

    monkeypatch.setattr("urllib.request.OpenerDirector.open", open_jwks)
    client = jwt.PyJWKClient(JWKS_URL, timeout=5)

    def configured_client(url):
        assert url == JWKS_URL
        return client

    monkeypatch.setattr(auth, "jwks_client", configured_client)
    state["client"] = client
    return state


@pytest.fixture
def token(signing_key):
    def make(changes=None, *, remove=(), key=None, headers=None):
        now = int(time.time())
        claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": "isolated-subject",
                  "exp": now + 600, "iat": now, "scope": "identity:read"}
        claims.update(changes or {})
        for name in remove:
            claims.pop(name, None)
        return jwt.encode(claims, key or signing_key, algorithm="RS256", headers={"kid": KID} | (headers or {}))
    return make


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path", ["/api/v1/me", "/api/v1/auth/session"])
def test_authentication_ignores_query_tokens_and_non_bearer_headers(path):
    with TestClient(create_app(), base_url="http://localhost") as client:
        for headers in ({}, {"Authorization": "Basic ignored"}, {"Authorization": "Bearer"}):
            response = client.get(path, params={"access_token": "ignored"}, headers=headers)
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == "Bearer"


def test_valid_session_exposes_only_public_validity_information(provider, token):
    access_token = token({"sub": "Case-Sensitive-Subject ", "private_claim": "DO_NOT_EXPOSE"})
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/auth/session", headers=bearer(access_token))
        identity = client.get("/api/v1/me", headers=bearer(access_token))
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"authenticated", "subject", "expires_at", "expires_in_seconds", "refresh_required"}
    assert data["authenticated"] is True
    assert data["subject"] == "Case-Sensitive-Subject "
    assert 590 <= data["expires_in_seconds"] <= 600
    assert datetime.fromisoformat(data["expires_at"]).utcoffset() == timedelta(0)
    assert data["refresh_required"] is False
    assert identity.json() == {"subject": "Case-Sensitive-Subject "}
    assert access_token not in response.text and "DO_NOT_EXPOSE" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert provider["requests"] == [JWKS_URL]  # Keys are cached, not authentication decisions.


@pytest.mark.parametrize(("remaining", "window", "refresh"), [(30, 60, True), (600, 60, False), (30, 10, False)])
def test_session_signals_renewal_in_the_configured_window(monkeypatch, provider, token, remaining, window, refresh):
    monkeypatch.setenv("OIDC_REFRESH_WINDOW_SECONDS", str(window))
    get_settings.cache_clear()
    access_token = token({"exp": int(time.time()) + remaining})
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/auth/session", headers=bearer(access_token))
    assert response.status_code == 200
    assert response.json()["refresh_required"] is refresh


@pytest.mark.parametrize("claim", ["exp", "iss", "aud", "sub"])
def test_required_claims_cannot_be_missing(provider, token, claim):
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(token(remove=[claim])))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Bearer error="invalid_token"'


@pytest.mark.parametrize(("claim", "value"), [
    ("iss", "https://another-issuer.example.test"), ("aud", "another-api"),
    ("exp", 1), ("exp", None), ("exp", "9999999999"), ("exp", float("nan")),
    ("exp", float("inf")), ("exp", True), ("sub", ""), ("sub", 10), ("sub", "x" * 256),
    ("nbf", 9999999999), ("iat", 9999999999), ("iat", "1"), ("nbf", "1"),
    ("scope", ["identity:read"]), ("scope", None), ("scope", "identity:read\nadmin"),
])
def test_invalid_claims_fail_closed(provider, token, claim, value):
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(token({claim: value})))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "http_401"


def test_wrong_signature_is_rejected(provider, token):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(token(key=other_key)))
    assert response.status_code == 401


@pytest.mark.parametrize("algorithm", ["HS256", "none"])
def test_unapproved_algorithms_are_rejected_before_jwks_fetch(provider, algorithm):
    access_token = jwt.encode({"sub": "ignored"}, os.urandom(32) if algorithm == "HS256" else None,
                              algorithm=algorithm, headers={"kid": KID})
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(access_token))
    assert response.status_code == 401
    assert provider["requests"] == []


@pytest.mark.parametrize("kid", [None, "", ["unexpected"]])
def test_invalid_key_identifiers_are_rejected_before_jwks_fetch(provider, kid):
    header = jwt.utils.base64url_encode(json.dumps({"alg": "RS256", "kid": kid}).encode()).decode()
    payload = jwt.utils.base64url_encode(b'{"sub":"ignored"}').decode()
    access_token = f"{header}.{payload}.aW52YWxpZA"
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(access_token))
    assert response.status_code == 401
    assert provider["requests"] == []


def test_token_cannot_choose_a_jwks_endpoint(provider, token):
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(token(headers={"jku": "https://untrusted.example.test/keys"})))
    assert response.status_code == 200
    assert provider["requests"] == [JWKS_URL]


def test_unknown_key_is_rejected_and_rotation_uses_the_configured_jwks(provider, token, signing_key):
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/api/v1/me", headers=bearer(token())).status_code == 200
        assert client.get("/api/v1/me", headers=bearer(token(headers={"kid": "unknown"}))).status_code == 401
        rotated = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key = jwt.algorithms.RSAAlgorithm.to_jwk(rotated.public_key(), as_dict=True)
        provider["keys"] = [key | {"kid": "rotated", "alg": "RS256", "use": "sig"}]
        jwks = provider["client"]
        jwks._last_successful_fetch = time.monotonic() - jwks.cooldown_duration - 1
        response = client.get("/api/v1/me", headers=bearer(token(key=rotated, headers={"kid": "rotated"})))
    assert response.status_code == 200
    assert set(provider["requests"]) == {JWKS_URL}


@pytest.mark.parametrize("changes", [{"scope": ""}, {"scope": "records:read"}, {"scope": "IDENTITY:READ", "roles": ["admin"]}])
def test_missing_exact_scope_is_forbidden(provider, token, changes):
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/auth/session", headers=bearer(token(changes)))
    assert response.status_code == 403
    assert response.headers["www-authenticate"] == 'Bearer error="insufficient_scope", scope="identity:read"'


def test_scp_claim_is_used_only_when_configured(monkeypatch, provider, token):
    access_token = token({"scope": "", "scp": "identity:read"})
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/api/v1/me", headers=bearer(access_token)).status_code == 403
    monkeypatch.setenv("OIDC_SCOPE_CLAIM", "scp")
    get_settings.cache_clear()
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/api/v1/me", headers=bearer(access_token)).status_code == 200


def test_all_required_scopes_are_checked_before_endpoint_execution(provider, token):
    app = create_app()
    calls = []

    @app.get("/api/v1/scoped-test")
    def operation(user: Annotated[AuthenticatedUser, Security(authenticate_request, scopes=["identity:read", "test:execute"])]):
        calls.append(user.subject)
        return {"executed": True}

    with TestClient(app, base_url="http://localhost") as client:
        for access_token, status in [("malformed", 401), (token({"exp": 1}), 401), (token(), 403)]:
            assert client.get("/api/v1/scoped-test", headers=bearer(access_token)).status_code == status
            assert calls == []
        response = client.get("/api/v1/scoped-test", headers=bearer(token({"scope": "identity:read test:execute"})))
    assert response.status_code == 200 and calls == ["isolated-subject"]


def test_expiration_is_rechecked_on_each_request(monkeypatch, provider, token):
    access_token = token()
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/api/v1/me", headers=bearer(access_token)).status_code == 200

        class Later(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(UTC) + timedelta(minutes=20)

        monkeypatch.setattr(jwt.api_jwt, "datetime", Later)
        response = client.get("/api/v1/me", headers=bearer(access_token))
    assert response.status_code == 401
    assert "expirado" in response.json()["error"]["message"]


def test_provider_outage_fails_closed_without_leaking_token_or_exception(monkeypatch, provider, token, caplog):
    def unavailable(*args, **kwargs):
        raise URLError("DO_NOT_LOG_PROVIDER_DETAILS")

    monkeypatch.setattr("urllib.request.OpenerDirector.open", unavailable)
    access_token = token()
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/auth/session", headers=bearer(access_token))
    assert response.status_code == 503
    assert "DO_NOT_LOG_PROVIDER_DETAILS" not in response.text + caplog.text
    assert access_token not in response.text + caplog.text


@pytest.mark.parametrize("response_body", [b"not-json", b'{"keys":[]}'])
def test_unusable_provider_keys_fail_closed(monkeypatch, provider, token, response_body):
    monkeypatch.setattr("urllib.request.OpenerDirector.open", lambda *args, **kwargs: io.BytesIO(response_body))
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(token()))
    assert response.status_code == 503


@pytest.mark.parametrize(("field", "value"), [("oidc_refresh_window_seconds", -1), ("oidc_refresh_window_seconds", 3601),
                                              ("oidc_scope_claim", "roles")])
def test_invalid_session_settings_are_rejected(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="mysql+pymysql://unused@localhost/review", **{field: value})
