import pytest

from prontuario_backend.models import medicamentos


@pytest.mark.parametrize(
    ("limite", "deslocamento", "erro"),
    [
        (-1, 0, ValueError),
        (1, -1, ValueError),
        (None, 0, TypeError),
        (1.5, 0, TypeError),
        (True, False, TypeError),
        (0, 0, ValueError),
        (101, 0, ValueError),
        (1, 100001, ValueError),
    ],
)
def test_listar_ativos_rejeita_paginacao_invalida_antes_de_acessar_banco(
    monkeypatch, limite, deslocamento, erro
):
    def banco_nao_deve_ser_acessado():
        pytest.fail("A validação deve acontecer antes da conexão com o banco")

    monkeypatch.setattr(medicamentos, "engine", banco_nao_deve_ser_acessado)

    with pytest.raises(erro):
        medicamentos.listar_ativos(limite, deslocamento)
