from sqlalchemy import text

from prontuario_backend.config.database import engine

SELECT_LEITO = """
SELECT id, unidade_id, codigo, situacao, criado_em
FROM cadastro__leitos
"""


def _buscar_por_id(connection, leito_id):
    row = connection.execute(
        text(SELECT_LEITO + " WHERE id = :id"),
        {"id": leito_id},
    ).mappings().one_or_none()
    return dict(row) if row else None


def buscar_por_id(leito_id):
    if not isinstance(leito_id, str) or not leito_id:
        return None
    with engine().connect() as connection:
        return _buscar_por_id(connection, leito_id)


def buscar_por_codigo(unidade_id, codigo):
    if (
        not isinstance(unidade_id, str)
        or not unidade_id
        or not isinstance(codigo, str)
        or not codigo
    ):
        return None
    with engine().connect() as connection:
        row = connection.execute(
            text(
                SELECT_LEITO
                + """
                WHERE unidade_id = :unidade_id AND codigo = :codigo
                """
            ),
            {"unidade_id": unidade_id, "codigo": codigo},
        ).mappings().one_or_none()
    return dict(row) if row else None


def listar_por_unidade(unidade_id, limite, deslocamento=0):
    if not isinstance(unidade_id, str) or not unidade_id:
        return []
    _validar_paginacao(limite, deslocamento)

    with engine().connect() as connection:
        rows = connection.execute(
            text(
                SELECT_LEITO
                + """
                WHERE unidade_id = :unidade_id
                ORDER BY codigo, id
                LIMIT :limite OFFSET :deslocamento
                """
            ),
            {
                "unidade_id": unidade_id,
                "limite": limite,
                "deslocamento": deslocamento,
            },
        ).mappings().all()
    return [dict(row) for row in rows]


def _validar_paginacao(limite, deslocamento):
    if isinstance(limite, bool) or not isinstance(limite, int) or limite < 0:
        raise ValueError("Limite da listagem deve ser um inteiro não negativo")
    if (
        isinstance(deslocamento, bool)
        or not isinstance(deslocamento, int)
        or deslocamento < 0
    ):
        raise ValueError("Deslocamento da listagem deve ser um inteiro não negativo")
