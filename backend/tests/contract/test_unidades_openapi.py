from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from prontuario_backend.main import create_app
from prontuario_backend.routes import unidades as unidades_routes
from prontuario_backend.views.errors import ErrorResponse

PATHS = {
    ("/api/v1/unidades", "post"): ("criar_unidade", "201"),
    ("/api/v1/unidades", "get"): ("listar_unidades", "200"),
    ("/api/v1/unidades/{id}", "get"): ("buscar_unidade", "200"),
    ("/api/v1/unidades/{id}", "patch"): ("atualizar_unidade", "200"),
    ("/api/v1/unidades/{id}", "delete"): ("desativar_unidade", "204"),
}


@pytest.fixture
def openapi_and_docs():
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        docs = client.get("/docs")
        return app.openapi(), docs


def test_unidades_routes_and_schemas_are_documented(openapi_and_docs):
    schema, docs = openapi_and_docs
    assert docs.status_code == 200
    assert "/openapi.json" in docs.text

    for (path, method), (operation_id, success_status) in PATHS.items():
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["tags"] == ["Unidades"]
        assert operation["summary"] and operation["description"]
        assert success_status in operation["responses"]
        assert operation.get("security") is None

    operations = schema["paths"]["/api/v1/unidades"]
    create = operations["post"]
    create_schema = schema["components"]["schemas"]["UnidadeCreate"]
    assert create_schema["additionalProperties"] is False
    assert create_schema["required"] == ["codigo", "nome", "tipo"]
    assert create_schema["properties"]["codigo"]["maxLength"] == 30
    assert create_schema["properties"]["nome"]["maxLength"] == 120
    assert create_schema["properties"]["tipo"]["maxLength"] == 40
    assert create_schema["examples"][0] == {
        "codigo": "UN-TESTE-01",
        "nome": "Unidade Escola",
        "tipo": "ensino",
    }
    assert (
        create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/UnidadeCreate"
    )
    assert (
        create["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/UnidadeResponse"
    )
    assert "409" in create["responses"] and "422" in create["responses"]
    assert (
        create["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )
    assert (
        create["responses"]["409"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )

    patch = schema["paths"]["/api/v1/unidades/{id}"]["patch"]
    patch_schema = schema["components"]["schemas"]["UnidadePatch"]
    assert patch_schema["additionalProperties"] is False
    assert "required" not in patch_schema
    assert patch_schema["properties"]["nome"]["type"] == "string"
    assert patch_schema["properties"]["tipo"]["type"] == "string"
    assert "404" in patch["responses"] and "422" in patch["responses"]

    response_schema = schema["components"]["schemas"]["UnidadeResponse"]
    assert response_schema["properties"]["id"]["format"] == "uuid"
    assert response_schema["properties"]["criado_em"]["format"] == "date-time"
    assert response_schema["properties"]["ativo"]["type"] == "integer"

    listing = operations["get"]
    page_ref = listing["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    page = schema["components"]["schemas"][page_ref.rsplit("/", 1)[-1]]
    assert page["properties"]["items"]["items"]["$ref"].endswith("/UnidadeResponse")
    assert "422" in listing["responses"]
    query = {parameter["name"]: parameter for parameter in listing["parameters"]}
    assert query["limit"]["in"] == query["offset"]["in"] == "query"
    assert query["limit"]["schema"]["default"] == 20
    assert query["offset"]["schema"]["maximum"] == 100000

    get_by_id = schema["paths"]["/api/v1/unidades/{id}"]["get"]
    id_parameter = get_by_id["parameters"][0]
    assert id_parameter["name"] == "id"
    assert id_parameter["schema"]["format"] == "uuid"
    assert "404" in get_by_id["responses"] and "422" in get_by_id["responses"]

    delete = schema["paths"]["/api/v1/unidades/{id}"]["delete"]["responses"]["204"]
    assert "content" not in delete


def test_listar_unidades_retorna_pagina_e_pagina_vazia(monkeypatch):
    rows = [
        {
            "id": str(uuid4()),
            "codigo": "UN-ATIVA-A",
            "nome": "Alfa",
            "tipo": "hospitalar",
            "ativo": 1,
            "criado_em": "2026-11-20T00:00:00",
        },
        {
            "id": str(uuid4()),
            "codigo": "UN-ATIVA-B",
            "nome": "Bravo",
            "tipo": "ambulatorio",
            "ativo": 1,
            "criado_em": "2026-11-20T00:00:00",
        },
    ]
    calls = []

    def listar(limit, offset):
        calls.append((limit, offset))
        return {
            "items": rows[offset : offset + limit],
            "total": len(rows),
            "limit": limit,
            "offset": offset,
        }

    monkeypatch.setattr(unidades_routes.unidades, "listar", listar)
    with TestClient(create_app(), base_url="http://localhost") as client:
        page = client.get("/api/v1/unidades", params={"limit": 1, "offset": 1})
        empty_page = client.get("/api/v1/unidades", params={"limit": 1, "offset": 5})

    assert page.status_code == empty_page.status_code == 200
    assert page.json()["items"][0]["nome"] == "Bravo"
    assert page.json()["total"] == 2
    assert page.json()["limit"] == 1 and page.json()["offset"] == 1
    assert empty_page.json() == {"items": [], "total": 2, "limit": 1, "offset": 5}
    assert calls == [(1, 1), (1, 5)]


def test_invalid_create_and_patch_inputs_fail_before_controller(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Dados inválidos não podem chamar o Controller")

    monkeypatch.setattr(unidades_routes.unidades, "criar", forbidden)
    monkeypatch.setattr(unidades_routes.unidades, "atualizar", forbidden)
    unit_id = str(uuid4())

    with TestClient(create_app(), base_url="http://localhost") as client:
        invalid_create = client.post(
            "/api/v1/unidades",
            json={
                "codigo": "UN-TESTE-01",
                "nome": "Unidade",
                "tipo": "ensino",
                "secret": "never-return-this",
            },
        )
        null_patch = client.patch(
            f"/api/v1/unidades/{unit_id}", json={"nome": None}
        )
        empty_patch = client.patch(f"/api/v1/unidades/{unit_id}", json={})
        invalid_uuid = client.get("/api/v1/unidades/not-a-uuid")

    for response in (invalid_create, null_patch, empty_patch, invalid_uuid):
        assert response.status_code == 422
        body = ErrorResponse.model_validate(response.json())
        assert body.error.code == "validation_error"
        assert str(body.error.request_id) == response.headers["x-request-id"]
        UUID(response.headers["x-request-id"])
    assert "never-return-this" not in invalid_create.text
