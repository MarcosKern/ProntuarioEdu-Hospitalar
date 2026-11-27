from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from prontuario_backend.main import create_app
from prontuario_backend.views.errors import ErrorResponse


def test_post_contexto_assistencial_cria_e_rejeita_codigo_duplicado(
    contextos_assistenciais,
):
    payload = {
        "codigo": "CTX-HTTP-01",
        "nome": "Contexto HTTP",
        "tipo_atendimento": "consulta",
    }
    invalid_payload = payload | {"unexpected": "field"}
    with TestClient(create_app(), base_url="http://localhost") as client:
        invalid = client.post(
            "/api/v1/contextos-assistenciais",
            json=invalid_payload,
        )
        created = client.post(
            "/api/v1/contextos-assistenciais",
            json=payload,
        )
        duplicate = client.post(
            "/api/v1/contextos-assistenciais",
            json=payload,
        )

    assert invalid.status_code == 422
    assert (
        ErrorResponse.model_validate(invalid.json()).error.code
        == "validation_error"
    )
    assert created.status_code == 201
    assert created.json()["codigo"] == payload["codigo"]
    assert created.json()["nome"] == payload["nome"]
    assert created.json()["nivel_cuidado"] is None
    assert created.json()["ativo"] == 1
    assert duplicate.status_code == 409
    assert (
        ErrorResponse.model_validate(duplicate.json()).error.message
        == "Código de contexto assistencial já cadastrado"
    )


def test_get_contextos_assistenciais_paginates_and_omits_inactive(
    contextos_assistenciais,
):
    with TestClient(create_app(), base_url="http://localhost") as client:
        first = client.get(
            "/api/v1/contextos-assistenciais",
            params={"limit": 1, "offset": 0},
        )
        second = client.get(
            "/api/v1/contextos-assistenciais",
            params={"limit": 1, "offset": 1},
        )
        empty = client.get(
            "/api/v1/contextos-assistenciais",
            params={"offset": 20},
        )
        invalid_pagination = client.get(
            "/api/v1/contextos-assistenciais",
            params={"limit": 0},
        )
        unexpected_filter = client.get(
            "/api/v1/contextos-assistenciais",
            params={"nome": "Alfa"},
        )

    assert (
        first.status_code
        == second.status_code
        == empty.status_code
        == 200
    )
    assert invalid_pagination.status_code == unexpected_filter.status_code == 422
    assert (
        ErrorResponse.model_validate(invalid_pagination.json()).error.code
        == "validation_error"
    )
    assert (
        ErrorResponse.model_validate(unexpected_filter.json()).error.code
        == "validation_error"
    )
    assert first.json()["total"] == second.json()["total"] == 3
    assert first.json()["items"][0]["nome"] == "Alfa"
    assert second.json()["items"][0]["nome"] == "Alfa"
    assert empty.json()["items"] == []
    assert all(
        item["ativo"] == 1
        for item in first.json()["items"] + second.json()["items"]
    )
    assert contextos_assistenciais[3]["id"] not in {
        item["id"]
        for item in first.json()["items"] + second.json()["items"]
    }


def test_get_contexto_assistencial_by_id_returns_not_found(
    contextos_assistenciais,
):
    with TestClient(create_app(), base_url="http://localhost") as client:
        found = client.get(
            f"/api/v1/contextos-assistenciais/{contextos_assistenciais[0]['id']}"
        )
        missing = client.get(
            f"/api/v1/contextos-assistenciais/{uuid4()}"
        )
        invalid_uuid = client.get(
            "/api/v1/contextos-assistenciais/not-a-uuid"
        )

    assert found.status_code == 200
    assert found.json()["id"] == contextos_assistenciais[0]["id"]
    assert missing.status_code == 404
    assert invalid_uuid.status_code == 422
    assert (
        ErrorResponse.model_validate(invalid_uuid.json()).error.code
        == "validation_error"
    )
    assert (
        ErrorResponse.model_validate(missing.json()).error.code
        == "http_404"
    )


def test_patch_contexto_assistencial_updates_and_clears_nivel(
    contextos_assistenciais,
):
    with TestClient(create_app(), base_url="http://localhost") as client:
        updated = client.patch(
            f"/api/v1/contextos-assistenciais/{contextos_assistenciais[1]['id']}",
            json={
                "nome": "Alfa atualizada",
                "nivel_cuidado": None,
            },
        )
        missing = client.patch(
            f"/api/v1/contextos-assistenciais/{uuid4()}",
            json={"tipo_atendimento": "ambulatorial"},
        )
        invalid_uuid = client.patch(
            "/api/v1/contextos-assistenciais/not-a-uuid",
            json={"nome": "Nome inválido"},
        )
        invalid_payload = client.patch(
            f"/api/v1/contextos-assistenciais/{contextos_assistenciais[1]['id']}",
            json={"nome": None},
        )
        empty_payload = client.patch(
            f"/api/v1/contextos-assistenciais/{contextos_assistenciais[1]['id']}",
            json={},
        )

    assert updated.status_code == 200
    assert updated.json()["id"] == contextos_assistenciais[1]["id"]
    assert updated.json()["codigo"] == contextos_assistenciais[1]["codigo"]
    assert updated.json()["nome"] == "Alfa atualizada"
    assert updated.json()["nivel_cuidado"] is None
    assert missing.status_code == 404
    assert invalid_uuid.status_code == 422
    assert invalid_payload.status_code == empty_payload.status_code == 422
    for response in (invalid_uuid, invalid_payload, empty_payload):
        assert (
            ErrorResponse.model_validate(response.json()).error.code
            == "validation_error"
        )


def test_delete_contexto_assistencial_returns_empty_204(
    contextos_assistenciais,
    application_schema,
):
    contexto_id = contextos_assistenciais[0]["id"]
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.delete(
            f"/api/v1/contextos-assistenciais/{contexto_id}"
        )
        missing = client.delete(
            f"/api/v1/contextos-assistenciais/{uuid4()}"
        )
        invalid_uuid = client.delete(
            "/api/v1/contextos-assistenciais/not-a-uuid"
        )

    assert response.status_code == 204
    assert response.content == b""
    assert missing.status_code == 404
    assert invalid_uuid.status_code == 422
    assert (
        ErrorResponse.model_validate(missing.json()).error.code
        == "http_404"
    )
    assert (
        ErrorResponse.model_validate(invalid_uuid.json()).error.code
        == "validation_error"
    )
    with application_schema.connect() as connection:
        row = connection.execute(
            text(
                "SELECT id, ativo FROM assistencial__contextos_assistenciais "
                "WHERE id = :id"
            ),
            {"id": contexto_id},
        ).mappings().one()
    assert row == {"id": contexto_id, "ativo": 0}
