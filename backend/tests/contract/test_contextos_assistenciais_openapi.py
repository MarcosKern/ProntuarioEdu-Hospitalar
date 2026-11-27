from uuid import UUID

from fastapi.testclient import TestClient

from prontuario_backend.main import create_app
from prontuario_backend.views.errors import ErrorResponse

PATHS = {
    ("/api/v1/contextos-assistenciais", "post"): (
        "criar_contexto_assistencial",
        "201",
    ),
    ("/api/v1/contextos-assistenciais", "get"): (
        "listar_contextos_assistenciais",
        "200",
    ),
    ("/api/v1/contextos-assistenciais/{id}", "get"): (
        "buscar_contexto_assistencial",
        "200",
    ),
    ("/api/v1/contextos-assistenciais/{id}", "patch"): (
        "atualizar_contexto_assistencial",
        "200",
    ),
    ("/api/v1/contextos-assistenciais/{id}", "delete"): (
        "desativar_contexto_assistencial",
        "204",
    ),
}


def test_contextos_assistenciais_routes_and_schemas_are_documented():
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        docs = client.get("/docs")
        schema = app.openapi()

    assert docs.status_code == 200
    assert "/openapi.json" in docs.text

    for (path, method), (operation_id, success_status) in PATHS.items():
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["tags"] == ["Contextos assistenciais"]
        assert operation["summary"] and operation["description"]
        assert success_status in operation["responses"]
        assert operation.get("security") is None

    create = schema["paths"]["/api/v1/contextos-assistenciais"]["post"]
    create_schema = schema["components"]["schemas"]["ContextoAssistencialCreate"]
    assert create_schema["additionalProperties"] is False
    assert create_schema["required"] == [
        "codigo",
        "nome",
        "tipo_atendimento",
    ]
    assert create_schema["properties"]["codigo"]["maxLength"] == 45
    assert create_schema["properties"]["nome"]["maxLength"] == 120
    assert create_schema["properties"]["tipo_atendimento"]["maxLength"] == 30
    nivel_create = create_schema["properties"]["nivel_cuidado"]["anyOf"]
    assert nivel_create[0]["maxLength"] == 50
    assert nivel_create[1]["type"] == "null"
    assert "409" in create["responses"] and "422" in create["responses"]
    assert (
        create["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ContextoAssistencialResponse"
    )

    patch = schema["paths"]["/api/v1/contextos-assistenciais/{id}"]["patch"]
    patch_schema = schema["components"]["schemas"]["ContextoAssistencialPatch"]
    assert patch_schema["additionalProperties"] is False
    assert "required" not in patch_schema
    assert patch_schema["properties"]["nome"]["type"] == "string"
    assert patch_schema["properties"]["tipo_atendimento"]["type"] == "string"
    assert "null" in patch_schema["properties"]["nivel_cuidado"]["anyOf"][1]["type"]
    assert "404" in patch["responses"] and "422" in patch["responses"]

    response_schema = schema["components"]["schemas"][
        "ContextoAssistencialResponse"
    ]
    assert response_schema["properties"]["id"]["format"] == "uuid"
    assert response_schema["properties"]["criado_em"]["format"] == "date-time"
    assert response_schema["properties"]["ativo"]["type"] == "integer"

    listing = schema["paths"]["/api/v1/contextos-assistenciais"]["get"]
    page_ref = listing["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    page = schema["components"]["schemas"][page_ref.rsplit("/", 1)[-1]]
    assert (
        page["properties"]["items"]["items"]["$ref"]
        .endswith("/ContextoAssistencialResponse")
    )
    query = {parameter["name"]: parameter for parameter in listing["parameters"]}
    assert query["limit"]["in"] == query["offset"]["in"] == "query"
    assert query["limit"]["schema"]["default"] == 20
    assert query["offset"]["schema"]["maximum"] == 100000

    get_by_id = schema["paths"]["/api/v1/contextos-assistenciais/{id}"]["get"]
    id_parameter = get_by_id["parameters"][0]
    assert id_parameter["name"] == "id"
    assert id_parameter["schema"]["format"] == "uuid"
    assert "404" in get_by_id["responses"] and "422" in get_by_id["responses"]

    delete = schema["paths"]["/api/v1/contextos-assistenciais/{id}"]["delete"]
    assert "204" in delete["responses"]
    assert "content" not in delete["responses"]["204"]


def test_invalid_contexto_inputs_fail_before_controller(monkeypatch):
    from prontuario_backend.routes import contextos_assistenciais as routes

    def forbidden(*args, **kwargs):
        raise AssertionError("Dados inválidos não podem chamar o Controller")

    monkeypatch.setattr(routes.contextos_assistenciais, "criar", forbidden)
    monkeypatch.setattr(routes.contextos_assistenciais, "atualizar", forbidden)
    context_id = str(UUID("00000000-0000-0000-0000-000000000001"))

    with TestClient(create_app(), base_url="http://localhost") as client:
        invalid_create = client.post(
            "/api/v1/contextos-assistenciais",
            json={
                "codigo": "CTX-TESTE-01",
                "nome": "Contexto",
                "tipo_atendimento": "consulta",
                "secret": "never-return-this",
            },
        )
        null_nome = client.patch(
            f"/api/v1/contextos-assistenciais/{context_id}",
            json={"nome": None},
        )
        empty_patch = client.patch(
            f"/api/v1/contextos-assistenciais/{context_id}",
            json={},
        )
        invalid_uuid = client.get(
            "/api/v1/contextos-assistenciais/not-a-uuid"
        )

    for response in (
        invalid_create,
        null_nome,
        empty_patch,
        invalid_uuid,
    ):
        assert response.status_code == 422
        body = ErrorResponse.model_validate(response.json())
        assert body.error.code == "validation_error"
        assert str(body.error.request_id) == response.headers["x-request-id"]
    assert "never-return-this" not in invalid_create.text
