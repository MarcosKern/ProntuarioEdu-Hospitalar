from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine
from prontuario_backend.models.contextos_assistenciais import (
    buscar_por_codigo,
    buscar_por_id,
    listar_ativos,
)

TABLE = "assistencial__contextos_assistenciais"


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
