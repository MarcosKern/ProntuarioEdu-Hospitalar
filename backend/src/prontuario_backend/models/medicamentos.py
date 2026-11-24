"""Consultas ao catálogo de medicamentos no MySQL."""

from sqlalchemy import text

from prontuario_backend.config.database import engine


def buscar_por_id(medicamento_id):
    with engine().connect() as connection:
        return (
            connection.execute(
                text("""
                    SELECT id, nome, principio_ativo, nome_comercial,
                           forma_farmaceutica, descricao, ativo, criado_em
                    FROM assistencial__medicamentos
                    WHERE id = :id
                """),
                {"id": medicamento_id},
            )
            .mappings()
            .one_or_none()
        )


def listar_ativos(limite: int, deslocamento: int, nome=None):
    """Lista ativos; nome é substring literal, com limite 1-100 e deslocamento 0-100000."""
    for parametro, valor in (
        ("limite", limite),
        ("deslocamento", deslocamento),
    ):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"{parametro} deve ser um inteiro")

    if not 1 <= limite <= 100:
        raise ValueError("limite deve estar entre 1 e 100")
    if not 0 <= deslocamento <= 100000:
        raise ValueError("deslocamento deve estar entre 0 e 100000")

    query = """
        SELECT id, nome, principio_ativo, nome_comercial,
               forma_farmaceutica, descricao, ativo, criado_em
        FROM assistencial__medicamentos
        WHERE ativo = 1
    """
    parametros = {"limite": limite, "deslocamento": deslocamento}

    if nome is not None:
        query += " AND nome LIKE :padrao ESCAPE '!'"
        nome_literal = (
            str(nome).replace("!", "!!").replace("%", "!%").replace("_", "!_")
        )
        parametros["padrao"] = f"%{nome_literal}%"

    query += " ORDER BY nome, id LIMIT :limite OFFSET :deslocamento"

    with engine().connect() as connection:
        return connection.execute(text(query), parametros).mappings().all()
