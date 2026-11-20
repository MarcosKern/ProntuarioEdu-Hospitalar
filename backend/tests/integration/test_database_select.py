from uuid import uuid4

import pytest
from sqlalchemy import text


@pytest.fixture
def unidade_teste(application_schema):
    unidade = {
        "id": str(uuid4()),
        "codigo": f"UN-TESTE-{uuid4().hex[:8]}",
        "nome": "Unidade fictícia de teste",
        "tipo": "hospital",
    }
    with application_schema.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO cadastro__unidades (id, codigo, nome, tipo) "
                "VALUES (:id, :codigo, :nome, :tipo)"
            ),
            unidade,
        )
    yield unidade
    with application_schema.begin() as connection:
        connection.execute(
            text("DELETE FROM cadastro__unidades WHERE id = :id"),
            {"id": unidade["id"]},
        )


def test_mysql_select_and_unit_lookup(application_schema, unidade_teste, mysql_url):
    with application_schema.connect() as sql:
        assert sql.execute(text("SELECT 1")).scalar_one() == 1

        rows = sql.execute(
            text(
                "SELECT id, codigo, nome FROM cadastro__unidades "
                "WHERE codigo = :codigo"
            ),
            {"codigo": unidade_teste["codigo"]},
        ).mappings().all()
        assert [dict(row) for row in rows] == [
            {
                "id": unidade_teste["id"],
                "codigo": unidade_teste["codigo"],
                "nome": unidade_teste["nome"],
            }
        ]

        missing_rows = sql.execute(
            text(
                "SELECT id, codigo, nome FROM cadastro__unidades "
                "WHERE codigo = :codigo"
            ),
            {"codigo": "UN-TESTE-AUSENTE"},
        ).mappings().all()
        assert missing_rows == []
