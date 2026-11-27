"""Consultas ao catálogo de medicamentos no MySQL."""

from uuid import uuid4

from sqlalchemy import text

from prontuario_backend.config.database import engine

SELECT_MEDICAMENTO = """
SELECT id, nome, principio_ativo, nome_comercial,
       forma_farmaceutica, descricao, ativo, criado_em
FROM assistencial__medicamentos
"""


def buscar_por_id(medicamento_id):
    with engine().connect() as connection:
        return (
            connection.execute(
                text(SELECT_MEDICAMENTO + " WHERE id = :id"),
                {"id": medicamento_id},
            )
            .mappings()
            .one_or_none()
        )


def listar_ativos(limite: int, deslocamento: int, nome=None):
    """Lista medicamentos ativos em ordem estável, usando substring literal."""
    _validar_paginacao(limite, deslocamento)
    where, parametros = _filtro_nome(nome)
    parametros.update({"limite": limite, "deslocamento": deslocamento})
    query = (
        SELECT_MEDICAMENTO
        + " WHERE ativo = 1"
        + where
        + " ORDER BY nome, id LIMIT :limite OFFSET :deslocamento"
    )

    with engine().connect() as connection:
        return connection.execute(text(query), parametros).mappings().all()


def listar_ativos_paginados(limite: int, deslocamento: int, nome=None):
    """Retorna itens e total sob o mesmo filtro e leitura consistente."""
    _validar_paginacao(limite, deslocamento)
    where, filtros = _filtro_nome(nome)
    parametros = filtros | {"limite": limite, "deslocamento": deslocamento}
    with engine().connect() as connection:
        with connection.begin():
            total = connection.execute(
                text(
                    "SELECT COUNT(*) FROM assistencial__medicamentos"
                    " WHERE ativo = 1"
                    + where
                ),
                filtros,
            ).scalar_one()
            rows = (
                connection.execute(
                    text(
                        SELECT_MEDICAMENTO
                        + " WHERE ativo = 1"
                        + where
                        + " ORDER BY nome, id LIMIT :limite OFFSET :deslocamento"
                    ),
                    parametros,
                )
                .mappings()
                .all()
            )
    return [dict(row) for row in rows], total


def criar(dados):
    medicamento_id = str(uuid4())
    with engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO assistencial__medicamentos
                    (id, nome, principio_ativo, nome_comercial,
                     forma_farmaceutica, descricao)
                VALUES
                    (:id, :nome, :principio_ativo, :nome_comercial,
                     :forma_farmaceutica, :descricao)
                """
            ),
            {
                "id": medicamento_id,
                "nome": dados["nome"],
                "principio_ativo": dados.get("principio_ativo"),
                "nome_comercial": dados.get("nome_comercial"),
                "forma_farmaceutica": dados.get("forma_farmaceutica"),
                "descricao": dados.get("descricao"),
            },
        )
        return _buscar_por_id(connection, medicamento_id)


def atualizar(medicamento_id, dados):
    if not isinstance(medicamento_id, str) or not medicamento_id:
        return None
    campos = {
        "nome",
        "principio_ativo",
        "nome_comercial",
        "forma_farmaceutica",
        "descricao",
    }
    if not dados or not set(dados).issubset(campos):
        raise ValueError("Atualização deve conter campos de medicamento válidos")

    with engine().begin() as connection:
        if _buscar_por_id(connection, medicamento_id) is None:
            return None
        assignments = ", ".join(f"{field} = :{field}" for field in dados)
        parameters = dict(dados)
        parameters["id"] = medicamento_id
        connection.execute(
            text(
                "UPDATE assistencial__medicamentos "
                f"SET {assignments} WHERE id = :id"
            ),
            parameters,
        )
        return _buscar_por_id(connection, medicamento_id)


def desativar(medicamento_id):
    if not isinstance(medicamento_id, str) or not medicamento_id:
        return None
    with engine().begin() as connection:
        if _buscar_por_id(connection, medicamento_id) is None:
            return None
        connection.execute(
            text(
                """
                UPDATE assistencial__medicamentos
                SET ativo = 0
                WHERE id = :id
                """
            ),
            {"id": medicamento_id},
        )
        return _buscar_por_id(connection, medicamento_id)


def _buscar_por_id(connection, medicamento_id):
    row = (
        connection.execute(
            text(SELECT_MEDICAMENTO + " WHERE id = :id"),
            {"id": medicamento_id},
        )
        .mappings()
        .one_or_none()
    )
    return dict(row) if row else None


def _filtro_nome(nome):
    if nome is None:
        return "", {}
    nome_literal = str(nome).replace("!", "!!").replace("%", "!%").replace("_", "!_")
    return " AND nome LIKE :padrao ESCAPE '!'", {"padrao": f"%{nome_literal}%"}


def _validar_paginacao(limite, deslocamento):
    for parametro, valor in (("limite", limite), ("deslocamento", deslocamento)):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"{parametro} deve ser um inteiro")

    if not 1 <= limite <= 100:
        raise ValueError("limite deve estar entre 1 e 100")
    if not 0 <= deslocamento <= 100000:
        raise ValueError("deslocamento deve estar entre 0 e 100000")
