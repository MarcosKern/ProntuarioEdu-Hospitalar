from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from prontuario_backend.models.unidades import (
    atualizar,
    buscar_por_codigo,
    buscar_por_id,
    criar,
    desativar,
    listar_ativas,
)


def test_criar_unidade(unidades):
    row = criar(
        {
            "codigo": "UN-TESTE-NOVA",
            "nome": "Nova unidade",
            "tipo": "hospitalar",
        }
    )

    assert row["id"]
    assert row["codigo"] == "UN-TESTE-NOVA"
    assert row["nome"] == "Nova unidade"
    assert row["tipo"] == "hospitalar"
    assert row["ativo"] == 1
    assert row["criado_em"] is not None
    assert buscar_por_id(row["id"]) == row


def test_criar_unidade_rejeita_codigo_repetido(unidades):
    with pytest.raises(IntegrityError):
        criar(
            {
                "codigo": unidades[0]["codigo"],
                "nome": "Duplicada",
                "tipo": "hospitalar",
            }
        )

    assert buscar_por_codigo(unidades[0]["codigo"])["nome"] == "Alfa"


def test_atualizar_unidade_preserva_id_e_codigo(unidades):
    row = atualizar(
        unidades[0]["id"],
        {"nome": "Alfa atualizada", "tipo": "ambulatorio"},
    )

    assert row["id"] == unidades[0]["id"]
    assert row["codigo"] == unidades[0]["codigo"]
    assert row["nome"] == "Alfa atualizada"
    assert row["tipo"] == "ambulatorio"


def test_atualizar_unidade_inexistente(unidades):
    assert atualizar(
        str(uuid4()), {"nome": "Inexistente", "tipo": "hospitalar"}
    ) is None


def test_desativar_unidade_mantem_registro_e_oculta_da_listagem(unidades):
    row = desativar(unidades[0]["id"])

    assert row["id"] == unidades[0]["id"]
    assert row["ativo"] == 0
    assert buscar_por_id(unidades[0]["id"])["ativo"] == 0
    assert unidades[0]["id"] not in {item["id"] for item in listar_ativas(10)}


def test_desativar_unidade_inexistente(unidades):
    assert desativar(str(uuid4())) is None
