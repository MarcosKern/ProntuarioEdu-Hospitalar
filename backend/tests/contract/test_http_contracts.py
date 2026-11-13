from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.engine import Engine

from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.controllers import auth
from prontuario_backend.main import create_app
from prontuario_backend.routes import api
from prontuario_backend.views.auth import IdentityResponse, TokenResponse
from prontuario_backend.views.errors import ERROR_RESPONSES, ErrorResponse
from prontuario_backend.views.pagination import PageResponse, PaginationParams


class ItemResponse(BaseModel):
    name: str


@pytest.fixture
def contract_app(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Contrato inválido não pode acessar banco nem executar a operação")

    monkeypatch.setattr(Engine, "connect", forbidden)
    monkeypatch.setattr(api, "refresh_access", forbidden)
    monkeypatch.setattr(api, "update_password", forbidden)
    app = create_app()
    app.dependency_overrides[authenticate_request] = lambda: AuthenticatedUser(
        str(uuid4()), datetime.now(UTC) + timedelta(minutes=5), frozenset({"identity:read"}))
    calls = []

    @app.get("/api/v1/contract/pages", response_model=PageResponse[ItemResponse], responses={422: ERROR_RESPONSES[422]})
    def pages(params: Annotated[PaginationParams, Query()]):
        calls.append(params)
        rows = [{"name": "first", "hash_senha": "must-not-escape"}, {"name": "second", "hash_senha": "must-not-escape"}]
        return {"items": rows[params.offset:params.offset + params.limit], "total": len(rows),
                "limit": params.limit, "offset": params.offset}

    return app, calls


def assert_error(response, status, code):
    assert response.status_code == status
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == code
    assert str(body.error.request_id) == response.headers["x-request-id"]
    UUID(response.headers["x-request-id"])
    assert response.headers["cache-control"] == "no-store"


def test_query_pagination_and_typed_response_are_reflected_in_http_and_openapi(contract_app):
    app, calls = contract_app
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/api/v1/contract/pages", params={"limit": 1, "offset": 1})
        assert response.status_code == 200
        assert response.json() == {"items": [{"name": "second"}], "total": 2, "limit": 1, "offset": 1}
        assert calls[0].limit == 1 and calls[0].offset == 1
        empty = client.get("/api/v1/contract/pages", params={"offset": 20})
        assert empty.json() == {"items": [], "total": 2, "limit": 20, "offset": 20}
        schema = client.get("/openapi.json").json()
    parameters = {field["name"]: field["schema"] for field in schema["paths"]["/api/v1/contract/pages"]["get"]["parameters"]}
    assert parameters["limit"]["default"] == 20 and parameters["limit"]["maximum"] == 100
    assert parameters["offset"]["minimum"] == 0 and parameters["offset"]["maximum"] == 100000


@pytest.mark.parametrize("query", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 100001},
                                    {"limit": "invalid"}, {"sort": "must-not-echo"}])
def test_invalid_pagination_is_rejected_before_the_operation(contract_app, query):
    app, calls = contract_app
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/api/v1/contract/pages", params=query)
    assert_error(response, 422, "validation_error")
    assert calls == []
    assert "must-not-echo" not in response.text


@pytest.mark.parametrize("path,payload", [
    ("refresh", {"refresh_token": "never-log-this-refresh", "user_id": "never-log-this-user"}),
    ("refresh", {"refresh_token": ""}),
    ("refresh", {"refresh_token": 123}),
    ("refresh", {"refresh_token": "never-log-this-refresh", "scope": "x" * 513}),
    ("password", {"current_password": "never-log-this-password", "new_password": "short"}),
    ("password", {"current_password": "never-log-this-password", "new_password": "new-valid-password", "admin": True}),
])
def test_json_validation_rejects_unknown_fields_types_and_sizes_without_leaking_input(contract_app, path, payload, caplog):
    app, _ = contract_app
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/auth/" + path, json=payload)
    assert_error(response, 422, "validation_error")
    assert "never-log-this" not in response.text + caplog.text
    assert "new-valid-password" not in response.text + caplog.text


def test_malformed_json_has_the_same_sanitized_error_envelope(contract_app, caplog):
    app, _ = contract_app
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/auth/refresh", content='{"refresh_token":"never-log-this"',
                               headers={"Content-Type": "application/json"})
    assert_error(response, 422, "validation_error")
    assert "never-log-this" not in response.text + caplog.text


@pytest.mark.parametrize("changes", [{"grant_type": "client_credentials"}, {"username": ""},
                                      {"password": ""}, {"scope": "x" * 513},
                                      {"role": "admin"}, {"client_secret": "never-log-this-secret"}])
def test_invalid_login_forms_are_rejected_before_login(contract_app, monkeypatch, changes, caplog):
    app, _ = contract_app

    def forbidden(*args, **kwargs):
        raise AssertionError("Formulário inválido não pode executar login")

    monkeypatch.setattr(auth, "login", forbidden)
    form = {"grant_type": "password", "username": "admin", "password": "never-log-this-password"} | changes
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/auth/token", data=form)
    assert_error(response, 400, "http_400")
    assert "never-log-this" not in response.text + caplog.text


@pytest.mark.parametrize("content_type", ["application/x-www-form-urlencoded", "Application/X-Www-Form-Urlencoded; charset=UTF-8"])
def test_valid_login_form_accepts_empty_swagger_client_fields(contract_app, monkeypatch, content_type):
    app, _ = contract_app
    calls = []

    def login(username, password, scope):
        calls.append((username, password, scope))
        return TokenResponse(access_token="isolated-access", refresh_token="isolated-refresh", expires_in=900, scope="identity:read")

    monkeypatch.setattr(auth, "login", login)
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/auth/token", data={"grant_type": "password", "username": "admin",
                               "password": "isolated-password", "scope": "identity:read", "client_id": "", "client_secret": ""},
                               headers={"Content-Type": content_type})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert calls == [("admin", "isolated-password", "identity:read")]


def test_invalid_percent_encoded_utf8_is_rejected_before_login(contract_app, monkeypatch):
    app, _ = contract_app

    def forbidden(*args, **kwargs):
        raise AssertionError("UTF-8 inválido não pode executar login")

    monkeypatch.setattr(auth, "login", forbidden)
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/auth/token", content="grant_type=password&username=admin&password=%FF",
                               headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert_error(response, 400, "http_400")


def test_repeated_form_fields_and_unsupported_content_types_are_documented_errors(contract_app):
    app, _ = contract_app
    with TestClient(app, base_url="http://localhost") as client:
        repeated = client.post("/api/v1/auth/token", content="grant_type=password&username=admin&username=other&password=never-log-this",
                               headers={"Content-Type": "application/x-www-form-urlencoded"})
        unsupported = client.post("/api/v1/auth/token", json={"password": "never-log-this"})
        schema = client.get("/openapi.json").json()
    assert_error(repeated, 400, "http_400")
    assert_error(unsupported, 415, "http_415")
    fields = schema["paths"]["/api/v1/auth/token"]["post"]["requestBody"]["content"]["application/x-www-form-urlencoded"]["schema"]
    assert fields["additionalProperties"] is False
    assert fields["properties"]["username"]["maxLength"] == 150
    assert fields["properties"]["scope"]["maxLength"] == 512
    assert fields["properties"]["password"]["format"] == "password"


def test_non_string_http_details_are_not_serialized_as_messages(contract_app, caplog):
    app, _ = contract_app

    @app.get("/api/v1/contract/error")
    def denied():
        raise HTTPException(403, {"password": "never-log-this"})

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/api/v1/contract/error")
    assert_error(response, 403, "http_403")
    assert isinstance(response.json()["error"]["message"], str)
    assert "never-log-this" not in response.text + caplog.text


def test_invalid_response_is_sanitized_before_reaching_the_client(contract_app, caplog):
    app, _ = contract_app

    @app.get("/api/v1/contract/invalid-response", response_model=IdentityResponse)
    def invalid_response():
        return {"subject": "never-log-this-invalid-response"}

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/api/v1/contract/invalid-response")
    assert_error(response, 500, "internal_error")
    assert "never-log-this-invalid-response" not in response.text + caplog.text
