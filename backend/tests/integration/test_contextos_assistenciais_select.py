import re
from pathlib import Path
from uuid import uuid4

import pytest
from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine
from prontuario_backend.models.contextos_assistenciais import (
    buscar_por_codigo,
    buscar_por_id,
    listar_ativos,
)

TABLE = "assistencial__contextos_assistenciais"


@pytest.fixture
def contextos_assistenciais(mysql_url):
    backend = Path(__file__).resolve().parents[2]
    source = (backend / "docs/database/prontuarioedu_mysql.sql").read_text()
    ddl = re.search(r"CREATE TABLE `" + TABLE + r"` \(.*?;", source, re.S)
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
            connection.execute(text(f"DROP TABLE IF EXISTS `{TABLE}`"))
            connection.execute(text(ddl.group()))
            connection.execute(
                text(
                    f"""
                    INSERT INTO `{TABLE}`
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
            connection.execute(text(f"DROP TABLE IF EXISTS `{TABLE}`"))


def test_buscar_por_id_encontra_registro_e_retorna_none_para_id_ausente(
    contextos_assistenciais,
):
    row = buscar_por_id(contextos_assistenciais[0]["id"])

    assert row["codigo"] == "CTX-TESTE-A2"
    assert row["tipo_atendimento"] == "ambulatorial"
    assert row["nivel_cuidado"] is None
    assert row["criado_em"] is not None
    assert buscar_por_id(str(uuid4())) is None


def test_buscar_por_codigo_retorna_tipo_e_nivel_de_cuidado(
    contextos_assistenciais,
):
    row = buscar_por_codigo("CTX-TESTE-A1")

    assert row["id"] == contextos_assistenciais[1]["id"]
    assert row["tipo_atendimento"] == "emergencia"
    assert row["nivel_cuidado"] == "urgencia"
    assert buscar_por_codigo("CTX-TESTE-INEXISTENTE") is None


def test_listar_ativos_ordena_por_nome_e_id_e_aplica_paginacao(
    contextos_assistenciais,
):
    first_page = listar_ativos(2)
    second_page = listar_ativos(2, 2)

    assert [row["id"] for row in first_page] == [
        contextos_assistenciais[1]["id"],
        contextos_assistenciais[0]["id"],
    ]
    assert [row["nome"] for row in second_page] == ["Bravo"]
    assert [row["id"] for row in listar_ativos(10)] == [
        contextos_assistenciais[1]["id"],
        contextos_assistenciais[0]["id"],
        contextos_assistenciais[2]["id"],
    ]


def test_listar_ativos_retorna_lista_vazia(contextos_assistenciais):
    with engine().begin() as connection:
        connection.execute(text(f"DELETE FROM `{TABLE}`"))

    assert listar_ativos(10) == []
