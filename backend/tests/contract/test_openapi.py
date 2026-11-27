import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app

OPERATIONS = {
    ("/health", "get"): ("check_health", "HealthResponse", 200, None),
    ("/api/v1/unidades", "post"): (
        "criar_unidade",
        "UnidadeResponse",
        201,
        None,
    ),
    ("/api/v1/unidades", "get"): (
        "listar_unidades",
        "PageResponse_UnidadeResponse_",
        200,
        None,
    ),
    ("/api/v1/unidades/{id}", "get"): (
        "buscar_unidade",
        "UnidadeResponse",
        200,
        None,
    ),
    ("/api/v1/unidades/{id}", "patch"): (
        "atualizar_unidade",
        "UnidadeResponse",
        200,
        None,
    ),
    ("/api/v1/unidades/{id}", "delete"): (
        "desativar_unidade",
        None,
        204,
        None,
    ),
    ("/api/v1/medicamentos", "post"): (
        "criar_medicamento",
        "MedicamentoResponse",
        201,
        None,
    ),
    ("/api/v1/medicamentos", "get"): (
        "listar_medicamentos",
        "PageResponse_MedicamentoResponse_",
        200,
        None,
    ),
    ("/api/v1/medicamentos/{id}", "get"): (
        "buscar_medicamento",
        "MedicamentoResponse",
        200,
        None,
    ),
    ("/api/v1/medicamentos/{id}", "patch"): (
        "atualizar_medicamento",
        "MedicamentoResponse",
        200,
        None,
    ),
    ("/api/v1/medicamentos/{id}", "delete"): (
        "desativar_medicamento",
    ("/api/v1/contextos-assistenciais", "post"): (
        "criar_contexto_assistencial",
        "ContextoAssistencialResponse",
        201,
        None,
    ),
    ("/api/v1/contextos-assistenciais", "get"): (
        "listar_contextos_assistenciais",
        "PageResponse_ContextoAssistencialResponse_",
        200,
        None,
    ),
    ("/api/v1/contextos-assistenciais/{id}", "get"): (
        "buscar_contexto_assistencial",
        "ContextoAssistencialResponse",
        200,
        None,
    ),
    ("/api/v1/contextos-assistenciais/{id}", "patch"): (
        "atualizar_contexto_assistencial",
        "ContextoAssistencialResponse",
        200,
        None,
    ),
    ("/api/v1/contextos-assistenciais/{id}", "delete"): (
        "desativar_contexto_assistencial",
        None,
        204,
        None,
    ),
    ("/api/v1/me", "get"): (
        "get_current_identity",
        "IdentityResponse",
        200,
        ["identity:read"],
    ),
    ("/api/v1/auth/session", "get"): (
        "get_session_status",
        "SessionResponse",
        200,
        ["identity:read"],
    ),
    ("/api/v1/admin/me", "get"): (
        "get_admin_identity",
        "AdministratorResponse",
        200,
        ["identity:read", "admin:access"],
    ),
    ("/api/v1/auth/token", "post"): ("login", "TokenResponse", 200, None),
    ("/api/v1/auth/refresh", "post"): ("refresh_access", "TokenResponse", 200, None),
    ("/api/v1/auth/logout", "post"): ("logout", None, 204, ["identity:read"]),
    (
        "/api/v1/auth/password",
        "post",
    ): ("change_password", None, 204, ["identity:read"]),
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
    for (path, method), (identifier, response_model, status, scopes) in OPERATIONS.items():
        operation = schema["paths"][path][method]
        assert operation["operationId"] == identifier
        assert operation["summary"] and operation["description"]
        identifiers.append(identifier)
        assert operation.get("security") == (
            [{"OAuth2PasswordBearer": scopes}, {"BearerToken": []}] if scopes else None
        )
        success = operation["responses"][str(status)]
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
