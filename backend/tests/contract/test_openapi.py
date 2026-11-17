import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app

OPERATIONS = {
    ("/health", "get"): ("check_health", "HealthResponse", None),
    ("/api/v1/me", "get"): (
        "get_current_identity",
        "IdentityResponse",
        ["identity:read"],
    ),
    ("/api/v1/auth/session", "get"): (
        "get_session_status",
        "SessionResponse",
        ["identity:read"],
    ),
    ("/api/v1/admin/me", "get"): (
        "get_admin_identity",
        "AdministratorResponse",
        ["identity:read", "admin:access"],
    ),
    ("/api/v1/auth/token", "post"): ("login", "TokenResponse", None),
    ("/api/v1/auth/refresh", "post"): ("refresh_access", "TokenResponse", None),
    ("/api/v1/auth/logout", "post"): ("logout", None, ["identity:read"]),
    ("/api/v1/auth/password", "post"): ("change_password", None, ["identity:read"]),
}


@pytest.fixture
def schema(monkeypatch):
    secret = "isolated-signing-secret-that-must-not-be-in-openapi"
    monkeypatch.setenv("AUTH_JWT_SECRET", secret)
    get_settings.cache_clear()

    def forbidden(*args, **kwargs):
        raise AssertionError("A documentação não pode conectar ao MySQL")

    monkeypatch.setattr(Engine, "connect", forbidden)
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert secret not in response.text
    return response.json()


def test_openapi_covers_public_operations_success_errors_and_scopes(schema):
    actual = {
        (path, method)
        for path, methods in schema["paths"].items()
        for method in methods
    }
    assert actual == set(OPERATIONS)
    identifiers = []
    for (path, method), (identifier, response_model, scopes) in OPERATIONS.items():
        operation = schema["paths"][path][method]
        assert operation["operationId"] == identifier
        assert operation["summary"] and operation["description"]
        identifiers.append(identifier)
        assert operation.get("security") == (
            [{"OAuth2PasswordBearer": scopes}] if scopes else None
        )
        success = operation["responses"]["200" if response_model else "204"]
        if response_model:
            assert success["content"]["application/json"]["schema"]["$ref"].endswith(
                "/" + response_model
            )
        else:
            assert "content" not in success
        for status in ("401", "403", "422", "429", "500", "503"):
            if status in operation["responses"]:
                assert operation["responses"][status]["content"]["application/json"][
                    "schema"
                ]["$ref"].endswith("/ErrorResponse")
    assert len(identifiers) == len(set(identifiers))


def test_openapi_references_resolve_and_export_preserves_the_contract(schema, tmp_path):
    def check(value):
        if isinstance(value, dict):
            if "$ref" in value:
                assert value["$ref"].startswith("#/")
                target = schema
                for part in value["$ref"][2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                assert target
            for nested in value.values():
                check(nested)
        elif isinstance(value, list):
            for nested in value:
                check(nested)

    check(schema)
    output = tmp_path / "openapi.json"
    output.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(output.read_text()) == schema


def test_openapi_documents_input_limits_identifiers_and_protocol_headers(schema):
    schemas = schema["components"]["schemas"]
    assert schemas["IdentityResponse"]["properties"]["subject"]["format"] == "uuid"
    assert schemas["ErrorDetail"]["properties"]["request_id"]["format"] == "uuid"
    assert schemas["RefreshRequest"]["additionalProperties"] is False
    assert schemas["RefreshRequest"]["properties"]["refresh_token"]["maxLength"] == 200
    password = schemas["PasswordChangeRequest"]["properties"]["new_password"]
    assert password["minLength"] == 12 and password["maxLength"] == 128
    assert password["writeOnly"] is True
    assert (
        "WWW-Authenticate"
        in schema["paths"]["/api/v1/me"]["get"]["responses"]["401"]["headers"]
    )
    assert (
        "Retry-After"
        in schema["paths"]["/api/v1/me"]["get"]["responses"]["429"]["headers"]
    )
