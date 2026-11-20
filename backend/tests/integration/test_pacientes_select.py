
from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine
from prontuario_backend.models.pacientes import (
    buscar_por_id,
    buscar_por_identificador,
    listar_ativos,
)


def criar_paciente(connection, nome, identificador, ativo=1):
    paciente_id = str(uuid4())

    connection.execute(
        text("""
            INSERT INTO cadastro__pacientes
                (id, identificador, nome, ativo, ficticio)
            VALUES
                (:id, :identificador, :nome, :ativo, 1)
        """),
        {
            "id": paciente_id,
            "identificador": identificador,
            "nome": nome,
            "ativo": ativo
        }
    )

    return paciente_id


def test_buscar_por_id(mysql_url, application_schema):
    paciente_id = str(uuid4())
    identificador = f"PAC-{uuid4().hex[:12]}"

    with engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO cadastro__pacientes
                    (id, identificador, nome, ativo, ficticio)
                VALUES
                    (:id, :identificador, :nome, 1, 1)
            """),
            {
                "id": paciente_id,
                "identificador": identificador,
                "nome": "Paciente Teste"
            }
        )

    try:
        paciente = buscar_por_id(paciente_id)

        assert paciente is not None
        assert paciente["id"] == paciente_id
        assert paciente["identificador"] == identificador

    finally:
        with engine().begin() as connection:
            connection.execute(
                text("""
                    DELETE FROM cadastro__pacientes
                    WHERE id = :id
                """),
                {"id": paciente_id}
            )


def test_buscar_por_identificador(mysql_url, application_schema):
    identificador = f"PAC-{uuid4().hex[:12]}"

    with engine().begin() as connection:
        paciente_id = criar_paciente(
            connection,
            "Paciente Identificador",
            identificador
        )

    try:
        paciente = buscar_por_identificador(identificador)

        assert paciente is not None
        assert paciente["identificador"] == identificador
        assert paciente["id"] == paciente_id

    finally:
        with engine().begin() as connection:
            connection.execute(
                text("""
                    DELETE FROM cadastro__pacientes
                    WHERE id = :id
                """),
                {"id": paciente_id}
            )


def test_buscar_por_id_ausente(mysql_url, application_schema):
    paciente = buscar_por_id(str(uuid4()))

    assert paciente is None


def test_buscar_por_identificador_ausente(
    mysql_url,
    application_schema
):
    paciente = buscar_por_identificador(
        f"PAC-{uuid4().hex[:12]}"
    )

    assert paciente is None


def test_listar_ativos_vazio(mysql_url, application_schema):
    prefixo = f"PAC-{uuid4().hex[:8]}"

    # Cria apenas pacientes inativos.
    with engine().begin() as connection:
        paciente_id = criar_paciente(
            connection,
            "Paciente Inativo",
            f"{prefixo}-001",
            ativo=0
        )

    try:
        # O paciente existe, mas não deve aparecer na listagem.
        pacientes = listar_ativos(10, 0)

        assert not any(
            paciente["id"] == paciente_id
            for paciente in pacientes
        )

    finally:
        with engine().begin() as connection:
            connection.execute(
                text("""
                    DELETE FROM cadastro__pacientes
                    WHERE id = :id
                """),
                {"id": paciente_id}
            )


def test_listar_ativos_ordenacao(mysql_url, application_schema):
    prefixo = f"PAC-{uuid4().hex[:8]}"

    pacientes_criados = []

    with engine().begin() as connection:
        # Inserção propositalmente fora da ordem alfabética.
        pacientes_criados.append(
            criar_paciente(
                connection, "Carlos", f"{prefixo}-003"
            )
        )

        pacientes_criados.append(
            criar_paciente(
                connection, "Ana", f"{prefixo}-001"
            )
        )

        pacientes_criados.append(
            criar_paciente(
                connection, "Bruno", f"{prefixo}-002"
            )
        )

    try:
        pacientes = listar_ativos(10, 0)

        # Considera somente os registros criados neste teste.
        ids_criados = set(pacientes_criados)

        pacientes_teste = [
            paciente
            for paciente in pacientes
            if paciente["id"] in ids_criados
        ]

        nomes = [
            paciente["nome"]
            for paciente in pacientes_teste
        ]

        assert nomes == ["Ana", "Bruno", "Carlos"]

    finally:
        with engine().begin() as connection:
            connection.execute(
                text("""
                    DELETE FROM cadastro__pacientes
                    WHERE id = :id
                """),
                [
                    {"id": paciente_id}
                    for paciente_id in pacientes_criados
                ]
            )
