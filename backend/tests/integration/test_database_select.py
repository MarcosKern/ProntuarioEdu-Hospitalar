from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine


def test_database_select_reference(mysql_url, application_schema):
    with engine().connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

        unit_id = str(uuid4())
        connection.execute(
            text(
                """
                INSERT INTO cadastro__unidades
                    (id, codigo, nome, tipo, ativo)
                VALUES
                    (:id, :codigo, :nome, :tipo, :ativo)
                """
            ),
            {
                "id": unit_id,
                "codigo": "UN-TESTE-01",
                "nome": "Unidade de Teste",
                "tipo": "hospitalar",
                "ativo": 1,
            },
        )
        connection.commit()

        found = connection.execute(
            text(
                """
                SELECT id, codigo, nome
                FROM cadastro__unidades
                WHERE codigo = :codigo
                """
            ),
            {"codigo": "UN-TESTE-01"},
        ).mappings().all()

        missing = connection.execute(
            text(
                """
                SELECT id, codigo, nome
                FROM cadastro__unidades
                WHERE codigo = :codigo
                """
            ),
            {"codigo": "UN-TESTE-INEXISTENTE"},
        ).mappings().all()

    assert found == [
        {
            "id": unit_id,
            "codigo": "UN-TESTE-01",
            "nome": "Unidade de Teste",
        }
    ]
    assert missing == []
