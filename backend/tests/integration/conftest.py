import re
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text

from prontuario_backend.config.database import engine


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


@pytest.fixture
def contextos_assistenciais(mysql_url):
    backend = Path(__file__).resolve().parents[2]
    source = (backend / "docs/database/prontuarioedu_mysql.sql").read_text()
    table = "assistencial__contextos_assistenciais"
    ddl = re.search(r"CREATE TABLE `" + table + r"` \(.*?;", source, re.S)
    assert ddl

    rows = [
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "codigo": "CTX-TESTE-A2",
            "nome": "Alfa",
            "tipo_atendimento": "ambulatorial",
            "nivel_cuidado": None,
            "ativo": 1,
        },
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "codigo": "CTX-TESTE-A1",
            "nome": "Alfa",
            "tipo_atendimento": "emergencia",
            "nivel_cuidado": "urgencia",
            "ativo": 1,
        },
        {
            "id": "00000000-0000-0000-0000-000000000003",
            "codigo": "CTX-TESTE-B",
            "nome": "Bravo",
            "tipo_atendimento": "internacao",
            "nivel_cuidado": "intensivo",
            "ativo": 1,
        },
        {
            "id": "00000000-0000-0000-0000-000000000004",
            "codigo": "CTX-TESTE-INATIVO",
            "nome": "Zeta",
            "tipo_atendimento": "internacao",
            "nivel_cuidado": "intensivo",
            "ativo": 0,
        },
    ]
    db = engine()

    try:
        with db.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            connection.execute(text(ddl.group()))
            connection.execute(
                text(
                    f"""
                    INSERT INTO `{table}`
                        (id, codigo, nome, tipo_atendimento, nivel_cuidado, ativo)
                    VALUES
                        (:id, :codigo, :nome, :tipo_atendimento, :nivel_cuidado, :ativo)
                    """
                ),
                rows,
            )
        yield rows
    finally:
        with db.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS `{table}`"))


@pytest.fixture
def medicamentos_schema(mysql_url):
    backend = Path(__file__).resolve().parents[2]
    source = (backend / "docs/database/prontuarioedu_mysql.sql").read_text()
    table = "assistencial__medicamentos"
    ddl = re.search(r"CREATE TABLE `" + table + r"` \(.*?;", source, re.S)
    assert ddl

    db = engine()
    with db.begin() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        connection.execute(text(ddl.group()))
    try:
        yield db
    finally:
        with db.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS `{table}`"))


@pytest.fixture
def medicamentos(medicamentos_schema):
    rows = [
        {
            "id": str(uuid4()),
            "nome": "Paracetamol",
            "principio_ativo": "Paracetamol",
            "nome_comercial": "Tylenol",
            "forma_farmaceutica": "Comprimido",
            "descricao": "Analgesico e antitermico",
            "ativo": 1,
        },
        {
            "id": str(uuid4()),
            "nome": "Dipirona",
            "principio_ativo": "Dipirona sodica",
            "nome_comercial": "Novalgina",
            "forma_farmaceutica": "Comprimido",
            "descricao": "Analgesico e antitermico",
            "ativo": 1,
        },
        {
            "id": str(uuid4()),
            "nome": "Amoxicilina",
            "principio_ativo": "Amoxicilina",
            "nome_comercial": None,
            "forma_farmaceutica": "Capsula",
            "descricao": None,
            "ativo": 0,
        },
    ]

    with medicamentos_schema.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO assistencial__medicamentos
                    (id, nome, principio_ativo, nome_comercial,
                    forma_farmaceutica, descricao, ativo)
                VALUES
                    (:id, :nome, :principio_ativo, :nome_comercial,
                    :forma_farmaceutica, :descricao, :ativo)
            """),
            rows,
        )

    return rows