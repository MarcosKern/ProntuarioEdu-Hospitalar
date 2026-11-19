from sqlalchemy import text

from prontuario_backend.config.database import engine


def buscar_por_id(id):
    sql=text("""
        SELECT id, identificador, nome, nascimento, sexo,
               ativo, ficticio, criado_em
        FROM cadastro__pacientes
        WHERE id = :id AND ficticio = 1
    """)

    with engine().connect() as connection:
        resultado = connection.execute(
            sql, 
            {"id": id}
            ).mappings().one_or_none()

        return resultado

def buscar_por_identificador(identificador):
    sql = text("""
        SELECT id, identificador, nome, nascimento, sexo,
               ativo, ficticio, criado_em
        FROM cadastro__pacientes
        WHERE identificador = :identificador
          AND ficticio = 1
        ORDER BY nome, id
    """)

    with engine().connect() as connection:
        resultado = connection.execute(
            sql,
            {"identificador": identificador}
        ).mappings().one_or_none

    return resultado

def listar_ativos(limite, deslocamento):
    sql = text ("""
        SELECT id, identificador, nome, nascimento, sexo,
               ativo, ficticio, criado_em
        FROM cadastro__pacientes
        WHERE ativo = 1 AND ficticio = 1
        ORDER BY nome, id
        LIMIT :limite OFFSET :deslocamento
    """)

    with engine().connect() as connection:
        resultados = connection.execute(
            sql,
            {
                "limite": limite,
                "deslocamento": deslocamento
            }
        ).mappings().all()

    return resultados

    