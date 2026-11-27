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
def leitos(application_schema, unidades):
    backend = Path(__file__).resolve().parents[2]
    source = (backend / "docs/database/prontuarioedu_mysql.sql").read_text()
    table = "cadastro__leitos"
    ddl = re.search(r"CREATE TABLE `" + table + r"` \(.*?;", source, re.S)
    assert ddl
    rows = [
        {
            "id": str(uuid4()),
            "unidade_id": unidades[0]["id"],
            "codigo": "B-02",
            "situacao": "ocupado",
        },
        {
            "id": str(uuid4()),
            "unidade_id": unidades[0]["id"],
            "codigo": "A-01",
            "situacao": "disponivel",
        },
        {
            "id": str(uuid4()),
            "unidade_id": unidades[1]["id"],
            "codigo": "A-01",
            "situacao": "higienizacao",
        },
    ]
    db = engine()

    try:
        with db.begin() as connection:
            connection.execute(text(ddl.group()))
            connection.execute(
                text(
                    """
                    ALTER TABLE `cadastro__leitos`
                    ADD CONSTRAINT `fk_cadastro_leitos_test`
                    FOREIGN KEY (unidade_id)
                    REFERENCES `cadastro__unidades`(id)
                    ON DELETE RESTRICT
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO cadastro__leitos
                        (id, unidade_id, codigo, situacao)
                    VALUES
                        (:id, :unidade_id, :codigo, :situacao)
                    """
                ),
                rows,
            )
        yield rows
    finally:
        with db.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS cadastro__leitos"))


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
