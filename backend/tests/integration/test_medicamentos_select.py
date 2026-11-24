import re
from pathlib import Path
from unittest.mock import MagicMock
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


def test_listar_ativos_filtra_inativos_ordena_e_aplica_paginacao(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        inserir_medicamento(connection, "Zinco")
        inserir_medicamento(connection, "Amoxicilina")
        inserir_medicamento(connection, "Azitromicina")
        inserir_medicamento(connection, "Aspirina inativa", ativo=0)
        inserir_medicamento(connection, "Paracetamol")

    assert [item["nome"] for item in listar_ativos(100, 0)] == [
        "Amoxicilina",
        "Azitromicina",
        "Paracetamol",
        "Zinco",
    ]
    assert [item["nome"] for item in listar_ativos(2, 0)] == [
        "Amoxicilina",
        "Azitromicina",
    ]
    assert [item["nome"] for item in listar_ativos(2, 2)] == ["Paracetamol", "Zinco"]
    assert listar_ativos(2, 4) == []
    assert listar_ativos(100, 100000) == []


def test_filtrar_nome_com_like_e_paginar(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        inserir_medicamento(connection, "Dipirona")
        inserir_medicamento(connection, "Dipirona sódica")
        inserir_medicamento(connection, "Paracetamol")

    pagina = listar_ativos(1, 1, "dipirona")
    assert len(pagina) == 1
    assert "Dipirona" in pagina[0]["nome"]


def test_filtrar_nome_trata_curingas_como_literais(medicamentos_schema):
    with medicamentos_schema.begin() as connection:
        inserir_medicamento(connection, "A%B")
        inserir_medicamento(connection, "A_B")
        inserir_medicamento(connection, "A!B")
        inserir_medicamento(connection, "ACB")

    assert [item["nome"] for item in listar_ativos(100, 0, "%")] == ["A%B"]
    assert [item["nome"] for item in listar_ativos(100, 0, "_")] == ["A_B"]
    assert [item["nome"] for item in listar_ativos(100, 0, "!")] == ["A!B"]


def test_listar_ativos_vincula_termo_de_busca_ao_sql(monkeypatch):
    database = MagicMock()
    connection = database.connect.return_value.__enter__.return_value
    connection.execute.return_value.mappings.return_value.all.return_value = []
    monkeypatch.setattr(
        "prontuario_backend.models.medicamentos.engine",
        lambda: database,
    )
    nome = "Dose d'água"

    assert listar_ativos(10, 0, nome) == []

    statement, parameters = connection.execute.call_args.args
    assert "nome LIKE :padrao" in statement.text
    assert "ESCAPE '!'" in statement.text
    assert nome not in statement.text
    assert parameters == {
        "limite": 10,
        "deslocamento": 0,
        "padrao": f"%{nome}%",
    }


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
def test_listar_ativos_rejeita_paginacao_invalida_antes_do_sql(
    medicamentos_schema, monkeypatch, limite, deslocamento, erro
):
    def banco_nao_deve_ser_acessado():
        pytest.fail("A validação deve acontecer antes da conexão com o banco")

    monkeypatch.setattr(
        "prontuario_backend.models.medicamentos.engine",
        banco_nao_deve_ser_acessado,
    )

    with pytest.raises(erro):
        listar_ativos(limite, deslocamento)
