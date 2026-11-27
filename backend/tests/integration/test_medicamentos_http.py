from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from prontuario_backend.main import create_app
from prontuario_backend.views.errors import ErrorResponse


def inserir_medicamento(connection, nome, *, ativo=1):
    medicamento_id = str(uuid4())
    connection.execute(
        text(
            """
            INSERT INTO assistencial__medicamentos (id, nome, ativo)
            VALUES (:id, :nome, :ativo)
            """
        ),
        {"id": medicamento_id, "nome": nome, "ativo": ativo},
    )
    return medicamento_id


def test_post_medicamentos_cria_nomes_duplicados_e_recusa_campos_extras(
    medicamentos_schema,
):
    payload = {
        "nome": "Medicamento de teste",
        "forma_farmaceutica": "comprimido",
    }
    with TestClient(create_app(), base_url="http://localhost") as client:
        invalid = client.post("/api/v1/medicamentos", json=payload | {"extra": "x"})
        first = client.post("/api/v1/medicamentos", json=payload)
        second = client.post("/api/v1/medicamentos", json=payload)

    assert invalid.status_code == 422
    assert ErrorResponse.model_validate(invalid.json()).error.code == "validation_error"
    assert first.status_code == second.status_code == 201
    assert first.json()["nome"] == second.json()["nome"] == payload["nome"]
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["ativo"] == 1
    assert first.json()["criado_em"]


def test_get_medicamentos_usa_filtro_ativo_literal_e_paginacao(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        inserir_medicamento(connection, "Dipirona")
        inserir_medicamento(connection, "Dipirona sódica")
        inserir_medicamento(connection, "Paracetamol")
        inserir_medicamento(connection, "Dipirona inativa", ativo=0)
        inserir_medicamento(connection, "A%B")
        inserir_medicamento(connection, "ACB")

    with TestClient(create_app(), base_url="http://localhost") as client:
        page = client.get(
            "/api/v1/medicamentos",
            params={"nome": "dipirona", "limit": 1, "offset": 1},
        )
        filtered = client.get(
            "/api/v1/medicamentos", params={"nome": "dipirona", "limit": 20}
        )
        wildcard = client.get("/api/v1/medicamentos", params={"nome": "%"})
        empty_page = client.get(
            "/api/v1/medicamentos",
            params={"nome": "dipirona", "limit": 1, "offset": 2},
        )

    assert (
        page.status_code
        == filtered.status_code
        == wildcard.status_code
        == empty_page.status_code
        == 200
    )
    assert page.json()["total"] == filtered.json()["total"] == 2
    assert page.json()["limit"] == 1 and page.json()["offset"] == 1
    assert len(page.json()["items"]) == 1
    assert len(filtered.json()["items"]) == 2
    assert all("Dipirona" in item["nome"] for item in filtered.json()["items"])
    assert [item["nome"] for item in wildcard.json()["items"]] == ["A%B"]
    assert empty_page.json() == {
        "items": [],
        "total": 2,
        "limit": 1,
        "offset": 2,
    }


def test_get_medicamento_by_id_returns_not_found(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        medicamento_id = inserir_medicamento(connection, "Medicamento consultado")

    with TestClient(create_app(), base_url="http://localhost") as client:
        found = client.get(f"/api/v1/medicamentos/{medicamento_id}")
        missing = client.get(f"/api/v1/medicamentos/{uuid4()}")
        invalid_uuid = client.get("/api/v1/medicamentos/not-a-uuid")

    assert found.status_code == 200
    assert found.json()["id"] == medicamento_id
    assert missing.status_code == 404
    assert ErrorResponse.model_validate(missing.json()).error.code == "http_404"
    assert invalid_uuid.status_code == 422
    assert (
        ErrorResponse.model_validate(invalid_uuid.json()).error.code
        == "validation_error"
    )


def test_patch_medicamento_updates_fields_and_allows_null_for_optional_fields(
    medicamentos_schema,
):
    with medicamentos_schema.begin() as connection:
        medicamento_id = inserir_medicamento(connection, "Nome original")

    with TestClient(create_app(), base_url="http://localhost") as client:
        updated = client.patch(
            f"/api/v1/medicamentos/{medicamento_id}",
            json={"nome": "Nome atualizado", "principio_ativo": None},
        )
        missing = client.patch(
            f"/api/v1/medicamentos/{uuid4()}", json={"nome": "Ausente"}
        )
        invalid = client.patch(
            f"/api/v1/medicamentos/{medicamento_id}", json={"nome": None}
        )

    assert updated.status_code == 200
    assert updated.json()["id"] == medicamento_id
    assert updated.json()["nome"] == "Nome atualizado"
    assert updated.json()["principio_ativo"] is None
    assert missing.status_code == 404
    assert invalid.status_code == 422
    assert ErrorResponse.model_validate(invalid.json()).error.code == (
        "validation_error"
    )


def test_delete_medicamento_returns_204_and_preserves_inactive_row(
    medicamentos_schema,
):
    with medicamentos_schema.begin() as connection:
        medicamento_id = inserir_medicamento(connection, "Medicamento desativado")

    with TestClient(create_app(), base_url="http://localhost") as client:
        deleted = client.delete(f"/api/v1/medicamentos/{medicamento_id}")
        missing = client.delete(f"/api/v1/medicamentos/{uuid4()}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert missing.status_code == 404
    with medicamentos_schema.connect() as connection:
        row = connection.execute(
            text("SELECT id, ativo FROM assistencial__medicamentos WHERE id = :id"),
            {"id": medicamento_id},
        ).mappings().one()
    assert row == {"id": medicamento_id, "ativo": 0}
