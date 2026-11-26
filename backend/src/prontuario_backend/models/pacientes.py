from sqlalchemy import text
from datetime import date
from uuid import uuid4


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


def _normalizar_nascimento(valor):
    """
    Converte uma data ISO para datetime.date.
    Aceita None quando o nascimento não foi informado.
    """
    if valor is None or valor == "":
        return None

    if isinstance(valor, date):
        return valor

    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ValueError("Nascimento deve estar no formato YYYY-MM-DD.")


def criar(dados):
    """
    Cria um paciente fictício e retorna os dados cadastrados.
    """

    paciente_id = str(uuid4())

    parametros = {
        "id": paciente_id,
        "identificador": dados["identificador"],
        "nome": dados["nome"],
        "nascimento": _normalizar_nascimento(dados.get("nascimento")),
        "sexo": dados.get("sexo") or None,
    }

    with engine().begin() as sql:
        sql.execute(
            text("""
                INSERT INTO cadastro__pacientes (
                    id,
                    identificador,
                    nome,
                    nascimento,
                    sexo,
                    ficticio
                )
                VALUES (
                    :id,
                    :identificador,
                    :nome,
                    :nascimento,
                    :sexo,
                    1
                )
            """),
            parametros,
        )

        resultado = (
            sql.execute(
                text("""
                SELECT
                    id,
                    identificador,
                    nome,
                    nascimento,
                    sexo,
                    ativo,
                    ficticio,
                    criado_em
                FROM cadastro__pacientes
                WHERE id = :id
                  AND ficticio = 1
            """),
                {"id": paciente_id},
            )
            .mappings()
            .first()
        )

        return dict(resultado) if resultado else None


def atualizar(id, dados):
    """
    Atualiza nome, nascimento e sexo de um paciente fictício.
    O identificador e o ID são preservados.
    """

    parametros = {
        "id": id,
        "nome": dados["nome"],
        "nascimento": _normalizar_nascimento(dados.get("nascimento")),
        "sexo": dados.get("sexo") or None,
    }

    with engine().begin() as sql:
        resultado = sql.execute(
            text("""
                UPDATE cadastro__pacientes
                SET
                    nome = :nome,
                    nascimento = :nascimento,
                    sexo = :sexo
                WHERE id = :id
                  AND ficticio = 1
            """),
            parametros,
        )

        if resultado.rowcount == 0:
            return None

        paciente = (
            sql.execute(
                text("""
                SELECT
                    id,
                    identificador,
                    nome,
                    nascimento,
                    sexo,
                    ativo,
                    ficticio,
                    criado_em
                FROM cadastro__pacientes
                WHERE id = :id
                  AND ficticio = 1
            """),
                {"id": id},
            )
            .mappings()
            .first()
        )

        return dict(paciente) if paciente else None


def desativar(id):
    """
    Desativa logicamente um paciente fictício.
    Não remove o registro do banco.
    """

    with engine().begin() as sql:
        resultado = sql.execute(
            text("""
                UPDATE cadastro__pacientes
                SET ativo = 0
                WHERE id = :id
                  AND ficticio = 1
            """),
            {"id": id},
        )

        return resultado.rowcount > 0
