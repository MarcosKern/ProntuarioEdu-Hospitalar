from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from prontuario_backend.models.contextos_assistenciais import (
    atualizar,
    buscar_por_codigo,
    buscar_por_id,
    criar,
    desativar,
    listar_ativos,
)


def test_criar_contexto_assistencial_com_nivel_nulo(contextos_assistenciais):
    row = criar(
        {
            "codigo": "CTX-TESTE-NOVO",
            "nome": "Novo contexto",
            "tipo_atendimento": "ambulatorial",
            "nivel_cuidado": None,
        }
    )

    assert row["id"]
    assert row["codigo"] == "CTX-TESTE-NOVO"
    assert row["nome"] == "Novo contexto"
    assert row["tipo_atendimento"] == "ambulatorial"
    assert row["nivel_cuidado"] is None
    assert row["ativo"] == 1
    assert row["criado_em"] is not None
    assert buscar_por_id(row["id"]) == row
    assert buscar_por_codigo(row["codigo"]) == row


def test_criar_contexto_assistencial_rejeita_codigo_repetido(
    contextos_assistenciais,
):
    with pytest.raises(IntegrityError):
        criar(
            {
                "codigo": contextos_assistenciais[0]["codigo"],
                "nome": "Duplicado",
                "tipo_atendimento": "internacao",
            }
        )

    assert buscar_por_codigo(contextos_assistenciais[0]["codigo"])["nome"] == "Alfa"


def test_atualizar_contexto_preserva_id_e_codigo(contextos_assistenciais):
    contexto = contextos_assistenciais[0]
    row = atualizar(
        contexto["id"],
        {
            "nome": "Alfa atualizado",
            "tipo_atendimento": "emergencia",
            "nivel_cuidado": "urgencia",
        },
    )

    assert row["id"] == contexto["id"]
    assert row["codigo"] == contexto["codigo"]
    assert row["nome"] == "Alfa atualizado"
    assert row["tipo_atendimento"] == "emergencia"
    assert row["nivel_cuidado"] == "urgencia"


def test_atualizar_contexto_inexistente(contextos_assistenciais):
    assert atualizar(
        str(uuid4()), {"nome": "Inexistente"}
    ) is None


def test_desativar_contexto_mantem_registro_e_oculta_da_listagem(
    contextos_assistenciais,
):
    contexto_id = contextos_assistenciais[0]["id"]
    row = desativar(contexto_id)

    assert row["id"] == contexto_id
    assert row["ativo"] == 0
    assert buscar_por_id(contexto_id)["ativo"] == 0
    assert contexto_id not in {item["id"] for item in listar_ativos(10)}


def test_desativar_contexto_inexistente(contextos_assistenciais):
    assert desativar(str(uuid4())) is None
