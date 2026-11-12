from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from prontuario_backend.config.auth import (
    AuthenticatedUser,
    authenticate_request,
    hash_password,
    verify_password,
)
from prontuario_backend.main import create_app
from prontuario_backend.models.users import bootstrap_system_admin, system_admin


def test_bootstrap_creates_an_application_admin_and_is_idempotent(application_schema, password_hash):
    subject = str(uuid4())
    assert bootstrap_system_admin(application_schema, subject, password_hash)['created'] is True
    assert bootstrap_system_admin(application_schema, subject, password_hash)['created'] is False
    with application_schema.connect() as connection:
        account = system_admin(connection, subject)
        assert account['id'] == subject and account['login'] == 'admin'
        assert connection.execute(text('SELECT COUNT(*) FROM cadastro__usuarios')).scalar_one() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM cadastro__usuario_perfil')).scalar_one() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM audit_events WHERE action="bootstrap_admin"')).scalar_one() == 1
        assert verify_password('Isolated-admin-password-123', connection.execute(text('SELECT hash_senha FROM cadastro__usuarios')).scalar_one())


def test_bootstrap_does_not_take_over_existing_admin(application_schema, password_hash):
    first, other = str(uuid4()), str(uuid4())
    bootstrap_system_admin(application_schema, first, password_hash)
    with pytest.raises(ValueError, match='preservado'):
        bootstrap_system_admin(application_schema, other, password_hash)
    with application_schema.connect() as connection:
        assert system_admin(connection, first)
        assert not system_admin(connection, other)


@pytest.mark.parametrize('statement', [
    'UPDATE cadastro__usuarios SET ativo=0',
    'UPDATE cadastro__usuario_perfil SET revogado_em=UTC_TIMESTAMP(6)',
    'DELETE FROM cadastro__perfil_permissao',
])
def test_revoked_account_or_permission_is_not_recreated_by_bootstrap(application_schema, password_hash, statement):
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject, password_hash)
    with application_schema.begin() as connection:
        connection.execute(text(statement))
    with pytest.raises(ValueError, match='nenhuma concessão'):
        bootstrap_system_admin(application_schema, subject, password_hash)
    with application_schema.connect() as connection:
        assert system_admin(connection, subject) is None


def test_admin_endpoint_checks_application_registration_and_active_profile(application_schema, password_hash):
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject, password_hash)
    app = create_app()
    user = AuthenticatedUser(subject, datetime.now(UTC) + timedelta(minutes=5), frozenset({'identity:read', 'admin:access'}))
    app.dependency_overrides[authenticate_request] = lambda: user
    with TestClient(app, base_url='http://localhost') as client:
        response = client.get('/api/v1/admin/me')
        assert response.status_code == 200
        assert response.json()['login'] == 'admin'
        assert response.json()['profile'] == 'ADMINISTRADOR'
        assert response.json()['permissions'] == ['USUARIO_GERENCIAR']
        with application_schema.begin() as connection:
            connection.execute(text('UPDATE cadastro__usuarios SET ativo=0 WHERE id=:id'), {'id': subject})
        assert client.get('/api/v1/admin/me').status_code == 403


def test_unknown_provider_subject_does_not_gain_admin_access(application_schema, password_hash):
    app = create_app()
    user = AuthenticatedUser(str(uuid4()), datetime.now(UTC) + timedelta(minutes=5), frozenset({'identity:read', 'admin:access'}))
    app.dependency_overrides[authenticate_request] = lambda: user
    with TestClient(app, base_url='http://localhost') as client:
        assert client.get('/api/v1/admin/me').status_code == 403


def test_admin_endpoint_fails_closed_without_application_schema():
    with TestClient(create_app(), base_url='http://localhost') as client:
        assert client.get('/api/v1/admin/me').status_code == 401


@pytest.fixture(scope="module")
def password_hash():
    return hash_password('Isolated-admin-password-123')


def test_external_admin_requires_explicit_conversion_and_keeps_identity(application_schema, password_hash):
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject, password_hash)
    with application_schema.begin() as connection:
        connection.execute(text("UPDATE cadastro__usuarios SET provedor='retired-provider', hash_senha=NULL"))
    with pytest.raises(ValueError, match='conversão explícita'):
        bootstrap_system_admin(application_schema, subject, password_hash)
    assert bootstrap_system_admin(application_schema, subject, password_hash, convert_existing=True)['user_id'] == subject
    with application_schema.connect() as connection:
        assert system_admin(connection, subject)['id'] == subject
        assert connection.execute(text('SELECT COUNT(*) FROM cadastro__usuarios')).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM audit_events WHERE action='local_admin_conversion'")).scalar_one() == 1


def test_conversion_does_not_restore_revoked_permission(application_schema, password_hash):
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject, password_hash)
    with application_schema.begin() as connection:
        connection.execute(text("UPDATE cadastro__usuarios SET provedor='retired-provider', hash_senha=NULL"))
        connection.execute(text("UPDATE cadastro__usuario_perfil SET revogado_em=UTC_TIMESTAMP(6)"))
    with pytest.raises(ValueError, match='nenhuma concessão'):
        bootstrap_system_admin(application_schema, subject, password_hash, convert_existing=True)
    with application_schema.connect() as connection:
        assert connection.execute(text('SELECT provedor FROM cadastro__usuarios')).scalar_one() == 'retired-provider'
        assert connection.execute(text("SELECT COUNT(*) FROM audit_events WHERE action='local_admin_conversion'")).scalar_one() == 0
