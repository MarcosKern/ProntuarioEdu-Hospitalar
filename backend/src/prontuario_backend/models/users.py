"""Cadastro e perfil do sistema; o login é realizado pelo provedor OIDC."""
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
    row = connection.execute(text("""
        SELECT u.id, u.login, u.nome
        FROM cadastro__usuarios u
        JOIN cadastro__usuario_perfil up ON up.usuario_id = u.id
        JOIN cadastro__perfis p ON p.id = up.perfil_id
        JOIN cadastro__perfil_permissao pp ON pp.perfil_id = p.id
        JOIN cadastro__permissoes permission ON permission.id = pp.permissao_id
        WHERE u.id = :subject AND u.provedor = 'keycloak' AND u.ativo = 1
          AND (u.bloqueado_ate IS NULL OR u.bloqueado_ate <= UTC_TIMESTAMP(6))
          AND up.revogado_em IS NULL AND up.unidade_id IS NULL
          AND p.codigo = 'ADMINISTRADOR' AND permission.codigo = 'USUARIO_GERENCIAR'
        LIMIT 1
    """), {"subject": subject}).mappings().first()
    return dict(row) if row else None


def bootstrap_system_admin(engine, subject):
    """Operação explícita, transacional e idempotente; não cria tabelas nem redefine senhas."""
    if str(UUID(subject)) != subject:
        raise ValueError("Identificador do administrador inválido")
    with engine.begin() as connection:
        existing = connection.execute(text(
            "SELECT id, login, provedor FROM cadastro__usuarios WHERE id = :id OR login = 'admin' FOR UPDATE"
        ), {"id": subject}).mappings().all()
        if existing:
            if len(existing) != 1 or existing[0]["id"] != subject or existing[0]["login"] != "admin" or existing[0]["provedor"] != "keycloak":
                raise ValueError("Já existe um usuário admin ou vínculo diferente; o cadastro foi preservado")
            if not system_admin(connection, subject):
                raise ValueError("O administrador existente está inativo ou sem permissão; nenhuma concessão foi refeita")
            return {"created": False, "user_id": subject, "login": "admin"}
        connection.execute(text("""
            INSERT INTO cadastro__usuarios (id, nome, login, provedor, ativo)
            VALUES (:id, 'Administrador do sistema', 'admin', 'keycloak', 1)
        """), {"id": subject})
        profile = connection.execute(text("SELECT id FROM cadastro__perfis WHERE codigo = 'ADMINISTRADOR'")).scalar_one_or_none()
        if not profile:
            profile = str(uuid4())
            connection.execute(text("""
                INSERT INTO cadastro__perfis (id, codigo, descricao)
                VALUES (:id, 'ADMINISTRADOR', 'Administração dos usuários do ProntuarioEdu')
            """), {"id": profile})
        permission = connection.execute(text("""
            SELECT id, recurso, acao FROM cadastro__permissoes WHERE codigo = 'USUARIO_GERENCIAR'
        """)).mappings().first()
        if permission and (permission["recurso"] != "usuarios" or permission["acao"] != "gerenciar"):
            raise ValueError("A permissão existente possui definição diferente; nenhuma alteração aplicada")
        permission_id = permission["id"] if permission else str(uuid4())
        if not permission:
            connection.execute(text("""
                INSERT INTO cadastro__permissoes (id, codigo, descricao, recurso, acao)
                VALUES (:id, 'USUARIO_GERENCIAR', 'Gerenciar usuários do sistema', 'usuarios', 'gerenciar')
            """), {"id": permission_id})
        connection.execute(text("""
            INSERT INTO cadastro__perfil_permissao (perfil_id, permissao_id)
            SELECT :profile, :permission WHERE NOT EXISTS (
                SELECT 1 FROM cadastro__perfil_permissao WHERE perfil_id = :profile AND permissao_id = :permission
            )
        """), {"profile": profile, "permission": permission_id})
        connection.execute(text("""
            INSERT INTO cadastro__usuario_perfil (id, usuario_id, perfil_id, concedido_por)
            VALUES (:id, :user, :profile, :user)
        """), {"id": str(uuid4()), "user": subject, "profile": profile})
        connection.execute(text("""
            INSERT INTO audit_events (id, occurred_at, subject, record_id, action, outcome, request_id)
            VALUES (:id, UTC_TIMESTAMP(6), :user, :user, 'bootstrap_admin', 'allowed', :request)
        """), {"id": str(uuid4()), "user": subject, "request": str(uuid4())})
        return {"created": True, "user_id": subject, "login": "admin"}
