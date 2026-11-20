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


def listar_ativos(limite, deslocamento, nome=None):
    query = """
        SELECT id, nome, principio_ativo, nome_comercial,
               forma_farmaceutica, descricao, ativo, criado_em
        FROM assistencial__medicamentos
        WHERE ativo = 1
    """
    parametros = {"limite": limite, "deslocamento": deslocamento}

    if nome is not None:
        query += " AND nome LIKE :padrao"
        parametros["padrao"] = f"%{nome}%"

    query += " ORDER BY nome, id LIMIT :limite OFFSET :deslocamento"

    with engine().connect() as connection:
        return (
            connection.execute(text(query), parametros)
            .mappings()
            .all()
        )
