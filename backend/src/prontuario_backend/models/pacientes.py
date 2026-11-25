from sqlalchemy import text

from prontuario_backend.config.database import engine

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_OFFSET = 100000


def buscar_por_id(id):
    sql = text("""
        SELECT id, identificador, nome, nascimento, sexo,
               ativo, ficticio, criado_em
        FROM cadastro__pacientes
        WHERE id = :id AND ficticio = 1
    """)

    with engine().connect() as connection:
        resultado = connection.execute(sql, {"id": id}).mappings().one_or_none()

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
        resultado = (
            connection.execute(sql, {"identificador": identificador})
            .mappings()
            .one_or_none()
        )

    return resultado


def buscar_por_nome(nome):
    if not isinstance(nome, str) or not nome.strip():
        raise ValueError("Nome para busca inválido")

    sql = text("""
        SELECT id, identificador, nome, nascimento, sexo,
               ativo, ficticio, criado_em
        FROM cadastro__pacientes
        WHERE nome LIKE :nome
          AND ficticio = 1
        ORDER BY nome, id
    """)

    with engine().connect() as connection:
        resultado = connection.execute(
            sql,
            {"nome": f"%{nome.strip()}%"},
        )

        return resultado.mappings().all()


def listar_ativos(limite=DEFAULT_LIMIT, deslocamento=0):
    if (
        isinstance(limite, bool)
        or not isinstance(limite, int)
        or limite <= 0
        or limite > MAX_LIMIT
    ):
        raise ValueError("Limite de paginação inválido")

    if (
        isinstance(deslocamento, bool)
        or not isinstance(deslocamento, int)
        or deslocamento < 0
        or deslocamento > MAX_OFFSET
    ):
        raise ValueError("Deslocamento de paginação inválido")

    sql = text("""
        SELECT *
        FROM cadastro__pacientes
        WHERE ativo = 1 AND ficticio = 1
        ORDER BY nome, id
        LIMIT :limite OFFSET :deslocamento
    """)

    with engine().connect() as connection:
        resultado = connection.execute(
            sql,
            {
                "limite": limite,
                "deslocamento": deslocamento,
            },
        )

        return resultado.mappings().all()
