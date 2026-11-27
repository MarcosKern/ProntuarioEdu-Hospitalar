from uuid import uuid4

import pytest

from prontuario_backend.models.leitos import (
    buscar_por_codigo,
    buscar_por_id,
    listar_por_unidade,
)


def test_buscar_por_id(leitos):
    row = buscar_por_id(leitos[0]["id"])

    assert row["id"] == leitos[0]["id"]
    assert row["unidade_id"] == leitos[0]["unidade_id"]
    assert row["codigo"] == "B-02"
    assert row["situacao"] == "ocupado"
    assert row["criado_em"] is not None
    assert buscar_por_id(str(uuid4())) is None


def test_buscar_por_codigo_e_permite_codigo_repetido_em_outras_unidades(
    leitos,
    unidades,
):
    row = buscar_por_codigo(unidades[1]["id"], "A-01")

    assert row["id"] == leitos[2]["id"]
    assert row["unidade_id"] == unidades[1]["id"]
    assert buscar_por_codigo(unidades[0]["id"], "INEXISTENTE") is None


def test_listar_por_unidade_ordena_e_aplica_paginacao(leitos, unidades):
    first = listar_por_unidade(unidades[0]["id"], 1, 0)
    second = listar_por_unidade(unidades[0]["id"], 1, 1)

    assert [row["codigo"] for row in first] == ["A-01"]
    assert [row["codigo"] for row in second] == ["B-02"]
    assert len(listar_por_unidade(unidades[1]["id"], 10)) == 1


def test_listar_por_unidade_retorna_vazio(leitos, unidades):
    assert listar_por_unidade(unidades[2]["id"], 10) == []


@pytest.mark.parametrize(
    ("limite", "deslocamento"),
    [(-1, 0), (True, 0), (10, -1), (10, True)],
)
def test_listar_por_unidade_rejeita_paginacao_invalida(
    unidades,
    limite,
    deslocamento,
):
    with pytest.raises(ValueError):
        listar_por_unidade(unidades[0]["id"], limite, deslocamento)
