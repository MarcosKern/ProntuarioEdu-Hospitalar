
from uuid import uuid4

import pytest
from sqlalchemy import text

from prontuario_backend.config.auth import hash_password
from prontuario_backend.models.users import (
    buscar_cadastro_por_id,
    listar_cadastros,
)


@pytest.fixture(scope="module")
def password_hash():
    return hash_password("Senha-Ficticia-123")


def inserir_usuario(application_schema, password_hash, ativo=1):
    usuario_id = str(uuid4())

    with application_schema.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO cadastro__usuarios
                    (id, nome, login, email, hash_senha, provedor, ativo)
                VALUES
                    (:id, :nome, :login, :email, :hash_senha, 'local', :ativo)
            """),
            {
                "id": usuario_id,
                "nome": "Usuario de Teste",
                "login": f"teste_{usuario_id[:8]}",
                "email": f"{usuario_id[:8]}@teste.local",
                "hash_senha": password_hash,
                "ativo": ativo,
            },
        )

    return usuario_id



def test_buscar_cadastro_por_id_retorna_apenas_campos_publicos(
    application_schema, password_hash
):
    usuario_id = inserir_usuario(application_schema, password_hash)

    cadastro = buscar_cadastro_por_id(usuario_id)

    assert cadastro is not None

    assert set(cadastro.keys()) == {
        "id",
        "nome",
        "login",
        "email",
        "ativo",
    }

    assert cadastro["id"] == usuario_id
    assert cadastro["nome"] == "Usuario de Teste"
    assert cadastro["ativo"] == 1


def test_buscar_cadastro_por_id_inexistente(application_schema):
    cadastro = buscar_cadastro_por_id(str(uuid4()))

    assert cadastro is None


def test_buscar_cadastro_por_id_inativo(application_schema, password_hash):
    usuario_id = inserir_usuario(
        application_schema,
        password_hash,
        ativo=0,
    )

    cadastro = buscar_cadastro_por_id(usuario_id)

    assert cadastro is not None
    assert cadastro["id"] == usuario_id
    assert cadastro["ativo"] == 0


def test_listar_cadastros_com_filtro_e_paginacao(
    application_schema, password_hash
):
    inserir_usuario(application_schema, password_hash, ativo=1)
    inserir_usuario(application_schema, password_hash, ativo=1)
    inserir_usuario(application_schema, password_hash, ativo=0)


    cadastros = listar_cadastros(limite=10, deslocamento=0)

    assert len(cadastros) == 3


    campos_publicos = {
        "id",
        "nome",
        "login",
        "email",
        "ativo",
    }

    for cadastro in cadastros:
        assert set(cadastro.keys()) == campos_publicos


    ordenados = sorted(
        cadastros,
        key=lambda cadastro: (cadastro["login"], cadastro["id"]),
    )
    assert cadastros == ordenados


    ativos = listar_cadastros(
        limite=10, deslocamento=0, ativo=1
    )
    assert len(ativos) == 2
    assert all(cadastro["ativo"] == 1 for cadastro in ativos)


    inativos = listar_cadastros(
        limite=10, deslocamento=0, ativo=0
    )
    assert len(inativos) == 1
    assert inativos[0]["ativo"] == 0


    primeira_pagina = listar_cadastros(
        limite=1, deslocamento=0
    )
    segunda_pagina = listar_cadastros(
        limite=1, deslocamento=1
    )

    assert len(primeira_pagina) == 1
    assert len(segunda_pagina) == 1
    assert primeira_pagina[0]["id"] != segunda_pagina[0]["id"]
