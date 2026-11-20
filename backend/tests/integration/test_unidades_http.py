from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from prontuario_backend.main import create_app
from prontuario_backend.views.errors import ErrorResponse


def test_post_unidades_cria_e_rejeita_codigo_duplicado(unidades):
    payload = {
        "codigo": "UN-HTTP-01",
        "nome": "Unidade HTTP",
        "tipo": "ensino",
    }
    invalid_payload = payload | {"unexpected": "field"}
    with TestClient(create_app(), base_url="http://localhost") as client:
        invalid = client.post("/api/v1/unidades", json=invalid_payload)
        created = client.post("/api/v1/unidades", json=payload)
        duplicate = client.post("/api/v1/unidades", json=payload)

    assert invalid.status_code == 422
    assert ErrorResponse.model_validate(invalid.json()).error.code == "validation_error"
    assert created.status_code == 201
    assert created.json()["codigo"] == payload["codigo"]
    assert created.json()["nome"] == payload["nome"]
    assert created.json()["ativo"] == 1
    assert duplicate.status_code == 409
    assert ErrorResponse.model_validate(duplicate.json()).error.message == (
        "Código de unidade já cadastrado"
    )


def test_get_unidades_paginates_counts_active_rows_and_returns_empty_page(unidades):
    with TestClient(create_app(), base_url="http://localhost") as client:
        first = client.get("/api/v1/unidades", params={"limit": 1, "offset": 0})
        second = client.get("/api/v1/unidades", params={"limit": 1, "offset": 1})
        empty = client.get("/api/v1/unidades", params={"offset": 20})

    assert first.status_code == second.status_code == empty.status_code == 200
    assert first.json()["total"] == second.json()["total"] == empty.json()["total"] == 2
    assert first.json()["items"][0]["nome"] == "Alfa"
    assert second.json()["items"][0]["nome"] == "Bravo"
    assert empty.json()["items"] == []
    assert first.json()["items"][0]["ativo"] == second.json()["items"][0]["ativo"] == 1
    assert unidades[2]["id"] not in {
        row["id"] for row in first.json()["items"] + second.json()["items"]
    }


def test_get_unidade_by_id_returns_not_found_for_missing_id(unidades):
    with TestClient(create_app(), base_url="http://localhost") as client:
        found = client.get(f"/api/v1/unidades/{unidades[0]['id']}")
        missing = client.get(f"/api/v1/unidades/{uuid4()}")

    assert found.status_code == 200
    assert found.json()["id"] == unidades[0]["id"]
    assert missing.status_code == 404
    assert ErrorResponse.model_validate(missing.json()).error.code == "http_404"


def test_patch_unidade_updates_only_supplied_fields(unidades):
    with TestClient(create_app(), base_url="http://localhost") as client:
        updated = client.patch(
            f"/api/v1/unidades/{unidades[0]['id']}",
            json={"nome": "Alfa atualizada"},
        )
        missing = client.patch(
            f"/api/v1/unidades/{uuid4()}",
            json={"tipo": "ensino"},
        )

    assert updated.status_code == 200
    assert updated.json()["id"] == unidades[0]["id"]
    assert updated.json()["codigo"] == unidades[0]["codigo"]
    assert updated.json()["nome"] == "Alfa atualizada"
    assert updated.json()["tipo"] == unidades[0]["tipo"]
    assert missing.status_code == 404


def test_delete_unidade_returns_empty_204_and_preserves_inactive_row(
    unidades, application_schema
):
    unit_id = unidades[0]["id"]
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.delete(f"/api/v1/unidades/{unit_id}")

    assert response.status_code == 204
    assert response.content == b""
    with application_schema.connect() as connection:
        row = connection.execute(
            text("SELECT id, ativo FROM cadastro__unidades WHERE id = :id"),
            {"id": unit_id},
        ).mappings().one()
    assert row == {"id": unit_id, "ativo": 0}
