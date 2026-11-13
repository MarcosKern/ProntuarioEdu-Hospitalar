import time
from contextlib import nullcontext
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from prontuario_backend.config import auth
from prontuario_backend.config.auth import hash_password, verify_password
from prontuario_backend.config.settings import Settings, get_settings
from prontuario_backend.main import create_app
from prontuario_backend.models.users import bootstrap_system_admin

SIGNING_SECRET = "isolated-test-signing-secret-with-more-than-32-bytes"
PASSWORD = "Isolated-admin-password-123"


def bearer(token):
    return {"Authorization": "Bearer " + token}


def login(client, password=PASSWORD, **extra):
    return client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": "admin",
            "password": password,
            "scope": "identity:read admin:access",
            **extra,
        },
    )


@pytest.fixture
def signed(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", SIGNING_SECRET)
    get_settings.cache_clear()
    monkeypatch.setattr(
        auth,
        "engine",
        lambda: type("Database", (), {"connect": lambda self: nullcontext(None)})(),
    )
    monkeypatch.setattr(
        auth, "active_session", lambda *args, **kwargs: {"id": str(uuid4())}
    )
    monkeypatch.setattr(auth, "system_admin", lambda *args: True)

    def token(changes=None, remove=(), key=SIGNING_SECRET):
        claims = {
            "iss": "prontuarioedu",
            "aud": "prontuario-api",
            "sub": str(uuid4()),
            "sid": str(uuid4()),
            "jti": str(uuid4()),
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
            "token_use": "access",
            "scope": "identity:read",
        }
        claims.update(changes or {})
        for field in remove:
            claims.pop(field)
        return jwt.encode(claims, key, algorithm="HS256")

    return token


@pytest.fixture(scope="module")
def password_hash():
    return hash_password(PASSWORD)


@pytest.fixture
def local_account(application_schema, password_hash, monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", SIGNING_SECRET)
    get_settings.cache_clear()
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject, password_hash)
    return application_schema, subject


@pytest.mark.parametrize(
    "path", ["/api/v1/me", "/api/v1/auth/session", "/api/v1/admin/me"]
)
def test_only_bearer_header_is_accepted(path):
    with TestClient(create_app(), base_url="http://localhost") as client:
        for headers in (
            {},
            {"Authorization": "Basic ignored"},
            {"Authorization": "Bearer"},
        ):
            assert (
                client.get(
                    path, params={"access_token": "ignored"}, headers=headers
                ).status_code
                == 401
            )


def test_valid_signed_session_and_refresh_window(signed):
    access = signed({"exp": int(time.time()) + 30})
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/auth/session", headers=bearer(access))
    assert response.status_code == 200
    assert response.json()["refresh_required"] is True
    assert 0 <= response.json()["expires_in_seconds"] <= 30
    assert access not in response.text
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "field", ["exp", "iat", "iss", "aud", "sub", "sid", "jti", "token_use", "scope"]
)
def test_required_claims(signed, field):
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert (
            client.get("/api/v1/me", headers=bearer(signed(remove=[field]))).status_code
            == 401
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("iss", "other"),
        ("aud", "other"),
        ("exp", 1),
        ("exp", None),
        ("exp", "9999999999"),
        ("exp", float("nan")),
        ("exp", float("inf")),
        ("exp", True),
        ("sub", ""),
        ("sub", 10),
        ("sid", "invalid"),
        ("iat", "1"),
        ("nbf", 9999999999),
        ("token_use", "refresh"),
        ("scope", ["identity:read"]),
        ("scope", None),
        ("scope", "records:read"),
    ],
)
def test_invalid_claims(signed, field, value):
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert (
            client.get("/api/v1/me", headers=bearer(signed({field: value}))).status_code
            == 401
        )


def test_invalid_signatures_and_scopes(signed):
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert (
            client.get(
                "/api/v1/me",
                headers=bearer(signed(key="other-test-key-of-at-least-32-bytes")),
            ).status_code
            == 401
        )
        assert (
            client.get(
                "/api/v1/me",
                headers=bearer(jwt.encode({"sub": "ignored"}, None, algorithm="none")),
            ).status_code
            == 401
        )
        assert (
            client.get("/api/v1/me", headers=bearer(signed({"scope": ""}))).status_code
            == 403
        )


def test_database_failure_is_closed_and_sanitized(signed, monkeypatch, caplog):
    def unavailable():
        raise SQLAlchemyError("DO_NOT_EXPOSE_DATABASE_SECRET")

    monkeypatch.setattr(auth, "engine", unavailable)
    token = signed()
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/v1/me", headers=bearer(token))
    assert response.status_code == 503
    assert "DO_NOT_EXPOSE_DATABASE_SECRET" not in response.text + caplog.text
    assert token not in response.text + caplog.text


def test_real_login_refresh_rotation_logout_and_hash_storage(local_account, caplog):
    database, subject = local_account
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = login(client)
        assert response.status_code == 200
        first = response.json()
        assert PASSWORD not in response.text + caplog.text
        assert (
            client.get(
                "/api/v1/admin/me", headers=bearer(first["access_token"])
            ).json()["subject"]
            == subject
        )
        with database.connect() as connection:
            stored = connection.execute(
                text("SELECT hash_senha FROM cadastro__usuarios")
            ).scalar_one()
            assert stored != PASSWORD and verify_password(PASSWORD, stored)
            assert (
                connection.execute(
                    text("SELECT refresh_token_hash FROM cadastro__sessoes_usuario")
                ).scalar_one()
                != first["refresh_token"]
            )
        rotated = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
        assert rotated.status_code == 200
        second = rotated.json()
        assert second["refresh_token"] != first["refresh_token"]
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/logout", headers=bearer(second["access_token"])
            ).status_code
            == 204
        )
        assert (
            client.get("/api/v1/me", headers=bearer(first["access_token"])).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
            ).status_code
            == 401
        )


def test_password_change_revokes_all_sessions(local_account):
    with TestClient(create_app(), base_url="http://localhost") as client:
        first, second = login(client).json(), login(client).json()
        headers = bearer(first["access_token"])
        assert (
            client.post(
                "/api/v1/auth/password",
                headers=headers,
                json={
                    "current_password": "incorrect",
                    "new_password": "New-isolated-password-456",
                },
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/password",
                headers=headers,
                json={
                    "current_password": PASSWORD,
                    "new_password": "New-isolated-password-456",
                },
            ).status_code
            == 204
        )
        for token in (first, second):
            assert (
                client.get(
                    "/api/v1/me", headers=bearer(token["access_token"])
                ).status_code
                == 401
            )
            assert (
                client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": token["refresh_token"]},
                ).status_code
                == 401
            )
        assert login(client).status_code == 401
        assert login(client, password="New-isolated-password-456").status_code == 200


def test_account_lockout_and_recovery(local_account):
    database, _ = local_account
    with TestClient(create_app(), base_url="http://localhost") as client:
        for _ in range(5):
            assert login(client, password="incorrect").status_code == 401
        assert login(client).status_code == 401
        with database.begin() as connection:
            assert (
                connection.execute(
                    text("SELECT falhas_login FROM cadastro__usuarios")
                ).scalar_one()
                == 5
            )
            connection.execute(
                text(
                    "UPDATE cadastro__usuarios SET bloqueado_ate=TIMESTAMPADD(MINUTE,-1,UTC_TIMESTAMP(6))"
                )
            )
        assert login(client).status_code == 200


@pytest.mark.parametrize(
    "statement,admin_status,identity_status",
    [
        ("UPDATE cadastro__usuarios SET ativo=0", 401, 401),
        (
            "UPDATE cadastro__sessoes_usuario SET expira_em=TIMESTAMPADD(SECOND,-1,UTC_TIMESTAMP(6))",
            401,
            401,
        ),
        ("UPDATE cadastro__usuario_perfil SET revogado_em=UTC_TIMESTAMP(6)", 403, 200),
    ],
)
def test_revocation_and_deactivation_are_immediate(
    local_account, statement, admin_status, identity_status
):
    database, _ = local_account
    with TestClient(create_app(), base_url="http://localhost") as client:
        credentials = login(client).json()
        with database.begin() as connection:
            connection.execute(text(statement))
        headers = bearer(credentials["access_token"])
        assert (
            client.get("/api/v1/admin/me", headers=headers).status_code == admin_status
        )
        assert client.get("/api/v1/me", headers=headers).status_code == identity_status


def test_login_rejects_ungranted_scopes_and_malformed_forms(local_account):
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert login(client, scope="arbitrary:admin").status_code == 400
        assert login(client, username="admin' OR 1=1 --").status_code == 401
        assert login(client, username="unknown-account").status_code == 401
        assert (
            client.post("/api/v1/auth/token", json={"password": PASSWORD}).status_code
            == 415
        )
        assert (
            client.post(
                "/api/v1/auth/token", data={"grant_type": "client_credentials"}
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": "malformed"}
            ).status_code
            == 401
        )


def test_scrypt_hashes_use_salts_and_reject_bad_passwords(password_hash):
    assert hash_password(PASSWORD) != password_hash
    assert not verify_password("incorrect", password_hash)
    assert not verify_password(PASSWORD, "malformed")
    with pytest.raises(ValueError):
        hash_password("short")


@pytest.mark.parametrize(
    "field,value",
    [
        ("auth_access_token_minutes", 0),
        ("auth_refresh_token_days", 31),
        ("auth_refresh_window_seconds", 3601),
        ("auth_jwt_secret", "short"),
    ],
)
def test_invalid_auth_settings(field, value):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="mysql+pymysql://unused@localhost/review",
            **{field: value},
        )
