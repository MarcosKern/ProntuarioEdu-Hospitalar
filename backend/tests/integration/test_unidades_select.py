from uuid import uuid4

import pytest

from prontuario_backend.models.unidades import (
    buscar_por_codigo,
    buscar_por_id,
    listar_ativas,
)


def test_buscar_por_id(unidades):
    row = buscar_por_id(unidades[0]["id"])

    assert row["id"] == unidades[0]["id"]
    assert row["codigo"] == "UN-TESTE-A"
    assert row["nome"] == "Alfa"
    assert row["tipo"] == "hospitalar"
    assert row["ativo"] == 1
    assert buscar_por_id(str(uuid4())) is None


def test_buscar_por_codigo(unidades):
    row = buscar_por_codigo("UN-TESTE-B")

    assert row["id"] == unidades[1]["id"]
    assert row["codigo"] == "UN-TESTE-B"
    assert buscar_por_codigo("UN-TESTE-INEXISTENTE") is None


def test_listar_ativas_ordenadas_e_paginadas(unidades):
    first = listar_ativas(1, 0)
    second = listar_ativas(1, 1)

    assert [row["nome"] for row in first] == ["Alfa"]
    assert [row["nome"] for row in second] == ["Bravo"]
    assert {row["nome"] for row in listar_ativas(10)} == {"Alfa", "Bravo"}


def test_listar_ativas_resultado_vazio(unidades):
    assert listar_ativas(10, 10) == []


@pytest.mark.parametrize(
    ("limite", "deslocamento"),
    [(-1, 0), (True, 0), (10, -1), (10, True)],
)
def test_listar_ativas_rejeita_paginacao_invalida(limite, deslocamento):
    with pytest.raises(ValueError):
        listar_ativas(limite, deslocamento)
