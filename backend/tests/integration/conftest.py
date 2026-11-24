from uuid import uuid4

import pytest
from sqlalchemy import text


@pytest.fixture
def unidades(application_schema):
    rows = [
        {
            "id": str(uuid4()),
            "codigo": "UN-TESTE-A",
            "nome": "Alfa",
            "tipo": "hospitalar",
            "ativo": 1,
        },
        {
            "id": str(uuid4()),
            "codigo": "UN-TESTE-B",
            "nome": "Bravo",
            "tipo": "ambulatorio",
            "ativo": 1,
        },
        {
            "id": str(uuid4()),
            "codigo": "UN-TESTE-C",
            "nome": "Chralie",
            "tipo": "hospitalar",
            "ativo": 0,
        },
    ]
    with application_schema.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO cadastro__unidades
                    (id, codigo, nome, tipo, ativo)
                VALUES
                    (:id, :codigo, :nome, :tipo, :ativo)
                """
            ),
            rows,
        )
    return rows
