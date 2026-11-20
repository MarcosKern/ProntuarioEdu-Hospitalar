from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine

SELECT_UNIDADE = """
SELECT id, codigo, nome, tipo, ativo, criado_em
FROM cadastro__unidades
"""


def _buscar_por_id(connection, unidade_id):
    row = connection.execute(
        text(SELECT_UNIDADE + " WHERE id = :id"),
        {"id": unidade_id},
    ).mappings().one_or_none()
    return dict(row) if row else None


def buscar_por_id(unidade_id):
    if not isinstance(unidade_id, str) or not unidade_id:
        return None
    with engine().connect() as connection:
        return _buscar_por_id(connection, unidade_id)


def buscar_por_codigo(codigo):
    if not isinstance(codigo, str) or not codigo:
        return None
    with engine().connect() as connection:
        row = connection.execute(
            text(SELECT_UNIDADE + " WHERE codigo = :codigo"),
            {"codigo": codigo},
        ).mappings().one_or_none()
    return dict(row) if row else None


def listar_ativas(limite, deslocamento=0):
    if isinstance(limite, bool) or not isinstance(limite, int) or limite < 0:
        raise ValueError("Limite da listagem deve ser um inteiro não negativo")
    if (
        isinstance(deslocamento, bool)
        or not isinstance(deslocamento, int)
        or deslocamento < 0
    ):
        raise ValueError("Deslocamento da listagem deve ser um inteiro não negativo")

    with engine().connect() as connection:
        rows = connection.execute(
            text(
                SELECT_UNIDADE
                + """
                WHERE ativo = 1
                ORDER BY nome, id
                LIMIT :limite OFFSET :deslocamento
                """
            ),
            {"limite": limite, "deslocamento": deslocamento},
        ).mappings().all()
    return [dict(row) for row in rows]


def criar(dados):
    unidade_id = str(uuid4())
    with engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO cadastro__unidades (id, codigo, nome, tipo)
                VALUES (:id, :codigo, :nome, :tipo)
                """
            ),
            {
                "id": unidade_id,
                "codigo": dados["codigo"],
                "nome": dados["nome"],
                "tipo": dados["tipo"],
            },
        )
        return _buscar_por_id(connection, unidade_id)


def atualizar(unidade_id, dados):
    if not isinstance(unidade_id, str) or not unidade_id:
        return None
    with engine().begin() as connection:
        if _buscar_por_id(connection, unidade_id) is None:
            return None
        connection.execute(
            text(
                """
                UPDATE cadastro__unidades
                SET nome = :nome, tipo = :tipo
                WHERE id = :id
                """
            ),
            {
                "id": unidade_id,
                "nome": dados["nome"],
                "tipo": dados["tipo"],
            },
        )
        return _buscar_por_id(connection, unidade_id)


def desativar(unidade_id):
    if not isinstance(unidade_id, str) or not unidade_id:
        return None
    with engine().begin() as connection:
        if _buscar_por_id(connection, unidade_id) is None:
            return None
        connection.execute(
            text(
                """
                UPDATE cadastro__unidades
                SET ativo = 0
                WHERE id = :id
                """
            ),
            {"id": unidade_id},
        )
        return _buscar_por_id(connection, unidade_id)
