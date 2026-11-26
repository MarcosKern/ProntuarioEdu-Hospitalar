from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine

SELECT_CONTEXTO = """
SELECT id, codigo, nome, tipo_atendimento, nivel_cuidado, ativo, criado_em
FROM assistencial__contextos_assistenciais
"""


def _buscar_por_id(connection, contexto_id):
    row = connection.execute(
        text(SELECT_CONTEXTO + " WHERE id = :id"),
        {"id": contexto_id},
    ).mappings().one_or_none()
    return dict(row) if row else None


def buscar_por_id(contexto_id):
    if not isinstance(contexto_id, str) or not contexto_id:
        return None
    with engine().connect() as connection:
        row = connection.execute(
            text(SELECT_CONTEXTO + " WHERE id = :id"),
            {"id": contexto_id},
        ).mappings().one_or_none()
    return dict(row) if row else None
        return _buscar_por_id(connection, contexto_id)


def buscar_por_codigo(codigo):
    if not isinstance(codigo, str) or not codigo:
        return None
    with engine().connect() as connection:
        row = connection.execute(
            text(SELECT_CONTEXTO + " WHERE codigo = :codigo ORDER BY nome, id"),
            {"codigo": codigo},
        ).mappings().one_or_none()
    return dict(row) if row else None


def listar_ativos(limite, deslocamento=0):
    _validar_paginacao(limite, deslocamento)

    with engine().connect() as connection:
        rows = connection.execute(
            text(
                SELECT_CONTEXTO
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
    contexto_id = str(uuid4())
    with engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO assistencial__contextos_assistenciais
                    (id, codigo, nome, tipo_atendimento, nivel_cuidado)
                VALUES
                    (:id, :codigo, :nome, :tipo_atendimento, :nivel_cuidado)
                """
            ),
            {
                "id": contexto_id,
                "codigo": dados["codigo"],
                "nome": dados["nome"],
                "tipo_atendimento": dados["tipo_atendimento"],
                "nivel_cuidado": dados.get("nivel_cuidado"),
            },
        )
        return _buscar_por_id(connection, contexto_id)


def atualizar(contexto_id, dados):
    if not isinstance(contexto_id, str) or not contexto_id:
        return None
    campos = {"nome", "tipo_atendimento", "nivel_cuidado"}
    if not dados or not set(dados).issubset(campos):
        raise ValueError("Atualização deve conter nome, tipo ou nível de cuidado")

    with engine().begin() as connection:
        if _buscar_por_id(connection, contexto_id) is None:
            return None
        assignments = ", ".join(f"{field} = :{field}" for field in dados)
        parameters = dict(dados)
        parameters["id"] = contexto_id
        connection.execute(
            text(
                "UPDATE assistencial__contextos_assistenciais "
                f"SET {assignments} WHERE id = :id"
            ),
            parameters,
        )
        return _buscar_por_id(connection, contexto_id)


def desativar(contexto_id):
    if not isinstance(contexto_id, str) or not contexto_id:
        return None
    with engine().begin() as connection:
        if _buscar_por_id(connection, contexto_id) is None:
            return None
        connection.execute(
            text(
                """
                UPDATE assistencial__contextos_assistenciais
                SET ativo = 0
                WHERE id = :id
                """
            ),
            {"id": contexto_id},
        )
        return _buscar_por_id(connection, contexto_id)


def _validar_paginacao(limite, deslocamento):
    if isinstance(limite, bool) or not isinstance(limite, int) or limite < 0:
        raise ValueError("Limite da listagem deve ser um inteiro não negativo")
    if (
        isinstance(deslocamento, bool)
        or not isinstance(deslocamento, int)
        or deslocamento < 0
    ):
        raise ValueError("Deslocamento da listagem deve ser um inteiro não negativo")
