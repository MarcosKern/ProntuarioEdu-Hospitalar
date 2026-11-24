from sqlalchemy import text

from prontuario_backend.config.database import engine

SELECT_CONTEXTO = """
SELECT id, codigo, nome, tipo_atendimento, nivel_cuidado, ativo, criado_em
FROM assistencial__contextos_assistenciais
"""


def buscar_por_id(contexto_id):
    if not isinstance(contexto_id, str) or not contexto_id:
        return None
    with engine().connect() as connection:
        row = connection.execute(
            text(SELECT_CONTEXTO + " WHERE id = :id"),
            {"id": contexto_id},
        ).mappings().one_or_none()
    return dict(row) if row else None


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


def _validar_paginacao(limite, deslocamento):
    if isinstance(limite, bool) or not isinstance(limite, int) or limite < 0:
        raise ValueError("Limite da listagem deve ser um inteiro não negativo")
    if (
        isinstance(deslocamento, bool)
        or not isinstance(deslocamento, int)
        or deslocamento < 0
    ):
        raise ValueError("Deslocamento da listagem deve ser um inteiro não negativo")
