from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from prontuario_backend.config.database import engine
from prontuario_backend.models.pacientes import (
    atualizar,
    buscar_por_id,
    buscar_por_identificador,
    criar,
    desativar,
    listar_ativos,
)


def novo_paciente(**alteracoes):
    dados = {
        "identificador": f"TESTE-{uuid4().hex[:12]}",
        "nome": "Paciente de Teste",
        "nascimento": "2000-05-15",
        "sexo": "Masculino",
    }

    dados.update(alteracoes)
    return dados


def test_criar_paciente(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        resultado = criar(dados)

        assert resultado is not None
        assert resultado["id"] is not None
        assert resultado["identificador"] == dados["identificador"]
        assert resultado["nome"] == dados["nome"]
        assert resultado["ficticio"] == 1
        assert resultado["ativo"] == 1

    finally:
        if "resultado" in locals() and resultado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": resultado["id"]},
                )


def test_criar_paciente_com_campos_opcionais_nulos(mysql_url, application_schema):
    dados = novo_paciente(
        nascimento=None,
        sexo=None,
    )

    try:
        resultado = criar(dados)

        assert resultado is not None
        assert resultado["nascimento"] is None
        assert resultado["sexo"] is None

    finally:
        if "resultado" in locals() and resultado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": resultado["id"]},
                )


def test_criar_paciente_com_identificador_duplicado(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        primeiro = criar(dados)

        with pytest.raises(IntegrityError):
            criar(dados)

        assert primeiro is not None

    finally:
        if "primeiro" in locals() and primeiro:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": primeiro["id"]},
                )


def test_buscar_paciente_criado_por_id(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        criado = criar(dados)

        resultado = buscar_por_id(criado["id"])

        assert resultado is not None
        assert resultado["id"] == criado["id"]
        assert resultado["identificador"] == dados["identificador"]

    finally:
        if "criado" in locals() and criado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": criado["id"]},
                )


def test_buscar_paciente_por_identificador(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        criado = criar(dados)

        resultado = buscar_por_identificador(dados["identificador"])

        assert resultado is not None
        assert resultado["id"] == criado["id"]

    finally:
        if "criado" in locals() and criado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": criado["id"]},
                )


def test_atualizar_paciente(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        criado = criar(dados)
        paciente_id = criado["id"]

        novos_dados = {
            "nome": "Paciente Atualizado",
            "nascimento": "1995-10-20",
            "sexo": "Feminino",
        }

        resultado = atualizar(
            paciente_id,
            novos_dados,
        )

        assert resultado is not None
        assert resultado["id"] == paciente_id
        assert resultado["identificador"] == dados["identificador"]
        assert resultado["nome"] == "Paciente Atualizado"
        assert resultado["nascimento"].isoformat() == "1995-10-20"
        assert resultado["sexo"] == "Feminino"

    finally:
        if "criado" in locals() and criado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": criado["id"]},
                )


def test_atualizar_paciente_com_id_inexistente(mysql_url, application_schema):
    resultado = atualizar(
        str(uuid4()),
        {
            "nome": "Paciente Inexistente",
            "nascimento": None,
            "sexo": None,
        },
    )

    assert resultado is None


def test_desativar_paciente(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        criado = criar(dados)

        resultado = desativar(criado["id"])

        assert resultado is True

        with engine().connect() as connection:
            paciente = (
                connection.execute(
                    text("""
                    SELECT ativo
                    FROM cadastro__pacientes
                    WHERE id = :id
                """),
                    {"id": criado["id"]},
                )
                .mappings()
                .first()
            )

        assert paciente is not None
        assert paciente["ativo"] == 0

    finally:
        if "criado" in locals() and criado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": criado["id"]},
                )


def test_desativar_paciente_com_id_inexistente(mysql_url, application_schema):
    resultado = desativar(str(uuid4()))

    assert resultado is False


def test_paciente_inativo_fora_da_listagem(mysql_url, application_schema):
    dados = novo_paciente()

    try:
        criado = criar(dados)

        desativar(criado["id"])

        resultado = listar_ativos(100, 0)

        ids = [paciente["id"] for paciente in resultado]

        assert criado["id"] not in ids

    finally:
        if "criado" in locals() and criado:
            with engine().begin() as connection:
                connection.execute(
                    text("""
                        DELETE FROM cadastro__pacientes
                        WHERE id = :id
                    """),
                    {"id": criado["id"]},
                )
