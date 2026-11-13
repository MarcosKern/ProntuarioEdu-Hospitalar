"""Cadastro, permissões e sessões de autenticação no MySQL."""

from uuid import UUID, uuid4

from sqlalchemy import text


def system_admin(connection, subject):
    if not isinstance(subject, str):
        return None
    try:
        if str(UUID(subject)) != subject:
            return None
    except ValueError:
        return None
    row = (
        connection.execute(
            text("""
        SELECT u.id, u.login, u.nome
        FROM cadastro__usuarios u
        JOIN cadastro__usuario_perfil up ON up.usuario_id = u.id
        JOIN cadastro__perfis p ON p.id = up.perfil_id
        JOIN cadastro__perfil_permissao pp ON pp.perfil_id = p.id
        JOIN cadastro__permissoes permission ON permission.id = pp.permissao_id
        WHERE u.id = :subject AND u.provedor = 'local' AND u.ativo = 1
          AND (u.bloqueado_ate IS NULL OR u.bloqueado_ate <= UTC_TIMESTAMP(6))
          AND up.revogado_em IS NULL AND up.unidade_id IS NULL
          AND p.codigo = 'ADMINISTRADOR' AND permission.codigo = 'USUARIO_GERENCIAR'
        LIMIT 1
    """),
            {"subject": subject},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def bootstrap_system_admin(engine, subject, password_hash, *, convert_existing=False):
    """Operação explícita, transacional e idempotente; não cria tabelas nem redefine senhas."""
    if str(UUID(subject)) != subject:
        raise ValueError("Identificador do administrador inválido")
    if not isinstance(password_hash, str) or not password_hash.startswith("scrypt$"):
        raise ValueError("O cadastro exige um hash scrypt, nunca a senha em texto")
    with engine.begin() as connection:
        existing = (
            connection.execute(
                text(
                    "SELECT id, login, provedor, ativo FROM cadastro__usuarios WHERE id = :id OR login = 'admin' FOR UPDATE"
                ),
                {"id": subject},
            )
            .mappings()
            .all()
        )
        if existing:
            if (
                len(existing) != 1
                or existing[0]["id"] != subject
                or existing[0]["login"] != "admin"
            ):
                raise ValueError(
                    "Já existe um usuário admin ou vínculo diferente; o cadastro foi preservado"
                )
            if existing[0]["provedor"] != "local":
                if not convert_existing or existing[0]["ativo"] != 1:
                    raise ValueError(
                        "Conta externa preservada; use a conversão explícita para login local"
                    )
                connection.execute(
                    text(
                        "UPDATE cadastro__usuarios SET provedor='local', hash_senha=:hash, senha_alterada_em=UTC_TIMESTAMP(6) WHERE id=:id"
                    ),
                    {"hash": password_hash, "id": subject},
                )
                connection.execute(
                    text("""
                    INSERT INTO audit_events (id, occurred_at, subject, record_id, action, outcome, request_id)
                    VALUES (:event, UTC_TIMESTAMP(6), :user, :user, 'local_admin_conversion', 'allowed', :request)
                """),
                    {"event": str(uuid4()), "user": subject, "request": str(uuid4())},
                )
            if not system_admin(connection, subject):
                raise ValueError(
                    "O administrador existente está inativo ou sem permissão; nenhuma concessão foi refeita"
                )
            return {"created": False, "user_id": subject, "login": "admin"}
        connection.execute(
            text("""
            INSERT INTO cadastro__usuarios (id, nome, login, provedor, ativo, hash_senha, senha_alterada_em)
            VALUES (:id, 'Administrador do sistema', 'admin', 'local', 1, :hash, UTC_TIMESTAMP(6))
        """),
            {"id": subject, "hash": password_hash},
        )
        profile = connection.execute(
            text("SELECT id FROM cadastro__perfis WHERE codigo = 'ADMINISTRADOR'")
        ).scalar_one_or_none()
        if not profile:
            profile = str(uuid4())
            connection.execute(
                text("""
                INSERT INTO cadastro__perfis (id, codigo, descricao)
                VALUES (:id, 'ADMINISTRADOR', 'Administração dos usuários do ProntuarioEdu')
            """),
                {"id": profile},
            )
        permission = (
            connection.execute(
                text("""
            SELECT id, recurso, acao FROM cadastro__permissoes WHERE codigo = 'USUARIO_GERENCIAR'
        """)
            )
            .mappings()
            .first()
        )
        if permission and (
            permission["recurso"] != "usuarios" or permission["acao"] != "gerenciar"
        ):
            raise ValueError(
                "A permissão existente possui definição diferente; nenhuma alteração aplicada"
            )
        permission_id = permission["id"] if permission else str(uuid4())
        if not permission:
            connection.execute(
                text("""
                INSERT INTO cadastro__permissoes (id, codigo, descricao, recurso, acao)
                VALUES (:id, 'USUARIO_GERENCIAR', 'Gerenciar usuários do sistema', 'usuarios', 'gerenciar')
            """),
                {"id": permission_id},
            )
        connection.execute(
            text("""
            INSERT INTO cadastro__perfil_permissao (perfil_id, permissao_id)
            SELECT :profile, :permission WHERE NOT EXISTS (
                SELECT 1 FROM cadastro__perfil_permissao WHERE perfil_id = :profile AND permissao_id = :permission
            )
        """),
            {"profile": profile, "permission": permission_id},
        )
        connection.execute(
            text("""
            INSERT INTO cadastro__usuario_perfil (id, usuario_id, perfil_id, concedido_por)
            VALUES (:id, :user, :profile, :user)
        """),
            {"id": str(uuid4()), "user": subject, "profile": profile},
        )
        connection.execute(
            text("""
            INSERT INTO audit_events (id, occurred_at, subject, record_id, action, outcome, request_id)
            VALUES (:id, UTC_TIMESTAMP(6), :user, :user, 'bootstrap_admin', 'allowed', :request)
        """),
            {"id": str(uuid4()), "user": subject, "request": str(uuid4())},
        )
        return {"created": True, "user_id": subject, "login": "admin"}


def account_for_login(connection, login):
    return (
        connection.execute(
            text("""
        SELECT id, login, hash_senha, ativo, provedor,
               (bloqueado_ate IS NOT NULL AND bloqueado_ate > UTC_TIMESTAMP(6)) AS bloqueado
        FROM cadastro__usuarios WHERE login=:login FOR UPDATE
    """),
            {"login": login},
        )
        .mappings()
        .first()
    )


def login_failure(connection, subject):
    connection.execute(
        text("""
        UPDATE cadastro__usuarios SET
          bloqueado_ate=CASE WHEN falhas_login+1 >= 5 THEN TIMESTAMPADD(MINUTE, 15, UTC_TIMESTAMP(6)) ELSE bloqueado_ate END,
          falhas_login=LEAST(falhas_login+1, 5)
        WHERE id=:id
    """),
        {"id": subject},
    )


def create_login_session(connection, subject, refresh_hash, expires, session_id):
    connection.execute(
        text("""
        UPDATE cadastro__usuarios SET falhas_login=0, bloqueado_ate=NULL, ultimo_login_em=UTC_TIMESTAMP(6) WHERE id=:id
    """),
        {"id": subject},
    )
    connection.execute(
        text("""
        INSERT INTO cadastro__sessoes_usuario (id, usuario_id, refresh_token_hash, expira_em, ultimo_uso_em)
        VALUES (:id, :user, :hash, :expires, UTC_TIMESTAMP(6))
    """),
        {"id": session_id, "user": subject, "hash": refresh_hash, "expires": expires},
    )


def active_session(connection, session_id, subject=None, *, lock=False):
    query = """
        SELECT s.id, s.usuario_id, s.refresh_token_hash, s.expira_em
        FROM cadastro__sessoes_usuario s JOIN cadastro__usuarios u ON u.id=s.usuario_id
        WHERE s.id=:id AND s.revogado_em IS NULL AND s.expira_em > UTC_TIMESTAMP(6)
          AND u.ativo=1 AND u.provedor='local'
          AND (u.bloqueado_ate IS NULL OR u.bloqueado_ate <= UTC_TIMESTAMP(6))
    """
    params = {"id": session_id}
    if subject is not None:
        query += " AND s.usuario_id=:subject"
        params["subject"] = subject
    if lock:
        query += " FOR UPDATE"
    return connection.execute(text(query), params).mappings().first()


def rotate_refresh(connection, session_id, refresh_hash):
    connection.execute(
        text("""
        UPDATE cadastro__sessoes_usuario SET refresh_token_hash=:hash, ultimo_uso_em=UTC_TIMESTAMP(6) WHERE id=:id
    """),
        {"id": session_id, "hash": refresh_hash},
    )


def revoke_session(connection, session_id, subject):
    connection.execute(
        text("""
        UPDATE cadastro__sessoes_usuario SET revogado_em=UTC_TIMESTAMP(6)
        WHERE id=:id AND usuario_id=:user AND revogado_em IS NULL
    """),
        {"id": session_id, "user": subject},
    )


def change_password(connection, subject, password_hash):
    connection.execute(
        text("""
        UPDATE cadastro__usuarios SET hash_senha=:hash, senha_alterada_em=UTC_TIMESTAMP(6) WHERE id=:id AND provedor='local'
    """),
        {"id": subject, "hash": password_hash},
    )
    connection.execute(
        text("""
        UPDATE cadastro__sessoes_usuario SET revogado_em=UTC_TIMESTAMP(6) WHERE usuario_id=:id AND revogado_em IS NULL
    """),
        {"id": subject},
    )


def account_password(connection, subject):
    return connection.execute(
        text(
            "SELECT hash_senha FROM cadastro__usuarios WHERE id=:id AND ativo=1 AND provedor='local' FOR UPDATE"
        ),
        {"id": subject},
    ).scalar_one_or_none()
