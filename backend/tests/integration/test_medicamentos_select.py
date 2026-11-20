import re
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text

from prontuario_backend.config.database import engine
from prontuario_backend.models.medicamentos import buscar_por_id, listar_ativos


@pytest.fixture
def medicamentos_schema(mysql_url):
    backend = Path(__file__).resolve().parents[2]
    source = (backend / "docs/database/prontuarioedu_mysql.sql").read_text()
    ddl = re.search(
        r"CREATE TABLE `assistencial__medicamentos` \(.*?;",
        source,
        re.S,
    )
    assert ddl

    db = engine()
    with db.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS assistencial__medicamentos"))
        connection.execute(text(ddl.group()))

    try:
        yield db
    finally:
        with db.begin() as connection:
            connection.execute(text("DROP TABLE assistencial__medicamentos"))


def inserir_medicamento(connection, nome, *, ativo=1, principio_ativo=None):
    medicamento_id = str(uuid4())
    connection.execute(
        text("""
            INSERT INTO assistencial__medicamentos
                (id, nome, principio_ativo, nome_comercial,
                 forma_farmaceutica, descricao, ativo)
            VALUES
                (:id, :nome, :principio_ativo, :nome_comercial,
                 :forma_farmaceutica, :descricao, :ativo)
        """),
        {
            "id": medicamento_id,
            "nome": nome,
            "principio_ativo": principio_ativo,
            "nome_comercial": None,
            "forma_farmaceutica": "comprimido",
            "descricao": "Catálogo de teste",
            "ativo": ativo,
        },
    )
    return medicamento_id


def test_buscar_por_id_retorna_catalogo_e_id_ausente(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        medicamento_id = inserir_medicamento(
            connection,
            "Amoxicilina",
            principio_ativo="Amoxicilina",
        )

    encontrado = buscar_por_id(medicamento_id)
    assert encontrado["id"] == medicamento_id
    assert encontrado["nome"] == "Amoxicilina"
    assert encontrado["principio_ativo"] == "Amoxicilina"
    assert encontrado["forma_farmaceutica"] == "comprimido"
    assert encontrado["descricao"] == "Catálogo de teste"
    assert buscar_por_id(str(uuid4())) is None


def test_listar_ativos_ordena_e_aplica_paginacao(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        inserir_medicamento(connection, "Zinco")
        inserir_medicamento(connection, "Amoxicilina")
        inserir_medicamento(connection, "Azitromicina")
        inserir_medicamento(connection, "Inativo", ativo=0)

    pagina = listar_ativos(2, 0)
    assert [item["nome"] for item in pagina] == ["Amoxicilina", "Azitromicina"]
    assert listar_ativos(10, 10) == []


def test_filtrar_nome_com_like_e_paginar(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        inserir_medicamento(connection, "Dipirona")
        inserir_medicamento(connection, "Dipirona sódica")
        inserir_medicamento(connection, "Paracetamol")

    pagina = listar_ativos(1, 1, "dipirona")
    assert len(pagina) == 1
    assert "Dipirona" in pagina[0]["nome"]
