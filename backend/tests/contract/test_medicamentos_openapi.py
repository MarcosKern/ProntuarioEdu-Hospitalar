import pytest
from fastapi.testclient import TestClient

from prontuario_backend.main import create_app
from prontuario_backend.routes import medicamentos as medicamentos_routes
from prontuario_backend.views.errors import ErrorResponse

PATHS = {
    ("/api/v1/medicamentos", "post"): ("criar_medicamento", "201"),
    ("/api/v1/medicamentos", "get"): ("listar_medicamentos", "200"),
    ("/api/v1/medicamentos/{id}", "get"): ("buscar_medicamento", "200"),
    ("/api/v1/medicamentos/{id}", "patch"): ("atualizar_medicamento", "200"),
    ("/api/v1/medicamentos/{id}", "delete"): ("desativar_medicamento", "204"),
}


@pytest.fixture
def openapi_and_docs():
    with TestClient(create_app(), base_url="http://localhost") as client:
        return client.get("/openapi.json").json(), client.get("/docs")


def _string_schema(properties, name):
    schema = properties[name]
    if "anyOf" in schema:
        return next(item for item in schema["anyOf"] if item.get("type") == "string")
    return schema


def test_medicamentos_routes_and_schemas_are_documented(openapi_and_docs):
    schema, docs = openapi_and_docs
    assert docs.status_code == 200
    assert "/openapi.json" in docs.text

    for (path, method), (operation_id, success_status) in PATHS.items():
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["tags"] == ["Medicamentos"]
        assert operation["summary"] and operation["description"]
        assert success_status in operation["responses"]
        assert operation.get("security") is None

    schemas = schema["components"]["schemas"]
    create = schema["paths"]["/api/v1/medicamentos"]["post"]
    create_schema = schemas["MedicamentoCreate"]
    assert create_schema["additionalProperties"] is False
    assert create_schema["required"] == ["nome"]
    assert create_schema["properties"]["nome"]["maxLength"] == 160
    assert _string_schema(create_schema["properties"], "principio_ativo")[
        "maxLength"
    ] == 160
    assert _string_schema(create_schema["properties"], "nome_comercial")[
        "maxLength"
    ] == 160
    assert _string_schema(create_schema["properties"], "forma_farmaceutica")[
        "maxLength"
    ] == 80
    assert create_schema["examples"][0] == {
        "nome": "Medicamento de demonstração",
        "forma_farmaceutica": "comprimido",
    }
    assert (
        create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/MedicamentoCreate"
    )
    assert "422" in create["responses"]

    patch = schema["paths"]["/api/v1/medicamentos/{id}"]["patch"]
    patch_schema = schemas["MedicamentoPatch"]
    assert patch_schema["additionalProperties"] is False
    assert "required" not in patch_schema
    assert patch_schema["properties"]["nome"]["type"] == "string"
    assert "422" in patch["responses"] and "404" in patch["responses"]

    response_schema = schemas["MedicamentoResponse"]
    assert response_schema["properties"]["id"]["format"] == "uuid"
    assert response_schema["properties"]["criado_em"]["format"] == "date-time"
    assert response_schema["properties"]["ativo"]["type"] == "integer"

    listing = schema["paths"]["/api/v1/medicamentos"]["get"]
    page_ref = listing["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    page = schemas[page_ref.rsplit("/", 1)[-1]]
    assert page["properties"]["items"]["items"]["$ref"].endswith(
        "/MedicamentoResponse"
    )
    query = {parameter["name"]: parameter for parameter in listing["parameters"]}
    assert {"limit", "offset", "nome"} <= query.keys()
    assert query["nome"]["in"] == "query"
    assert query["limit"]["schema"]["default"] == 20
    assert query["offset"]["schema"]["maximum"] == 100000

    for method in ("get", "patch", "delete"):
        operation = schema["paths"]["/api/v1/medicamentos/{id}"][method]
        assert "404" in operation["responses"]
        assert operation["parameters"][0]["schema"]["format"] == "uuid"
    delete = schema["paths"]["/api/v1/medicamentos/{id}"]["delete"]["responses"][
        "204"
    ]
    assert "content" not in delete


def test_invalid_medicamento_inputs_fail_before_controller(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Dados inválidos não podem chamar o Controller")

    monkeypatch.setattr(medicamentos_routes.medicamentos, "criar", forbidden)
    monkeypatch.setattr(medicamentos_routes.medicamentos, "atualizar", forbidden)

    with TestClient(create_app(), base_url="http://localhost") as client:
        invalid_create = client.post(
            "/api/v1/medicamentos",
            json={"nome": "Medicamento", "extra": "never-return-this"},
        )
        null_name = client.patch(
            "/api/v1/medicamentos/00000000-0000-0000-0000-000000000001",
            json={"nome": None},
        )
        empty_patch = client.patch(
            "/api/v1/medicamentos/00000000-0000-0000-0000-000000000001",
            json={},
        )
        invalid_uuid = client.get("/api/v1/medicamentos/not-a-uuid")

    for response in (invalid_create, null_name, empty_patch, invalid_uuid):
        assert response.status_code == 422
        body = ErrorResponse.model_validate(response.json())
        assert body.error.code == "validation_error"
        assert str(body.error.request_id) == response.headers["x-request-id"]
    assert "never-return-this" not in invalid_create.text
