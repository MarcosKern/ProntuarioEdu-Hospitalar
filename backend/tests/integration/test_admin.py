import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.config.database import engine
from prontuario_backend.main import create_app
from prontuario_backend.models.users import bootstrap_system_admin, system_admin

TABLES = ['cadastro__unidades', 'cadastro__profissionais', 'cadastro__usuarios', 'cadastro__perfis',
          'cadastro__permissoes', 'cadastro__perfil_permissao', 'cadastro__usuario_perfil']


@pytest.fixture
def application_schema(mysql_url):
    backend = Path(__file__).resolve().parents[2]
    command.upgrade(Config(str(backend / 'alembic.ini')), 'head')
    source = (backend / 'docs/database/prontuarioedu_mysql.sql').read_text()
    db = engine()
    with db.begin() as connection:
        for table in TABLES:
            ddl = re.search(r'CREATE TABLE `' + table + r'` \(.*?;', source, re.S)
            assert ddl
            connection.execute(text(ddl.group()))
        for match in re.finditer(r'ALTER TABLE `([^`]+)`[^;]+;', source):
            if match[1] in TABLES:
                connection.execute(text(match.group()))
        for match in re.finditer(r'CREATE UNIQUE INDEX [^;]+ ON `([^`]+)`[^;]+;', source):
            if match[1] in TABLES:
                connection.execute(text(match.group()))
    try:
        yield db
    finally:
        with db.begin() as connection:
            for table in reversed(TABLES):
                connection.execute(text('DROP TABLE ' + table))


def test_bootstrap_creates_an_application_admin_and_is_idempotent(application_schema):
    subject = str(uuid4())
    assert bootstrap_system_admin(application_schema, subject)['created'] is True
    assert bootstrap_system_admin(application_schema, subject)['created'] is False
    with application_schema.connect() as connection:
        account = system_admin(connection, subject)
        assert account['id'] == subject and account['login'] == 'admin'
        assert connection.execute(text('SELECT COUNT(*) FROM cadastro__usuarios')).scalar_one() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM cadastro__usuario_perfil')).scalar_one() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM audit_events WHERE action="bootstrap_admin"')).scalar_one() == 1
        assert connection.execute(text('SELECT hash_senha FROM cadastro__usuarios')).scalar_one() is None


def test_bootstrap_does_not_take_over_existing_admin(application_schema):
    first, other = str(uuid4()), str(uuid4())
    bootstrap_system_admin(application_schema, first)
    with pytest.raises(ValueError, match='preservado'):
        bootstrap_system_admin(application_schema, other)
    with application_schema.connect() as connection:
        assert system_admin(connection, first)
        assert not system_admin(connection, other)


@pytest.mark.parametrize('statement', [
    'UPDATE cadastro__usuarios SET ativo=0',
    'UPDATE cadastro__usuario_perfil SET revogado_em=UTC_TIMESTAMP(6)',
    'DELETE FROM cadastro__perfil_permissao',
])
def test_revoked_account_or_permission_is_not_recreated_by_bootstrap(application_schema, statement):
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject)
    with application_schema.begin() as connection:
        connection.execute(text(statement))
    with pytest.raises(ValueError, match='nenhuma concessão'):
        bootstrap_system_admin(application_schema, subject)
    with application_schema.connect() as connection:
        assert system_admin(connection, subject) is None


def test_admin_endpoint_checks_application_registration_and_active_profile(application_schema):
    subject = str(uuid4())
    bootstrap_system_admin(application_schema, subject)
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


def test_unknown_provider_subject_does_not_gain_admin_access(application_schema):
    app = create_app()
    user = AuthenticatedUser(str(uuid4()), datetime.now(UTC) + timedelta(minutes=5), frozenset({'identity:read', 'admin:access'}))
    app.dependency_overrides[authenticate_request] = lambda: user
    with TestClient(app, base_url='http://localhost') as client:
        assert client.get('/api/v1/admin/me').status_code == 403


def test_admin_endpoint_fails_closed_without_application_schema():
    with TestClient(create_app(), base_url='http://localhost') as client:
        assert client.get('/api/v1/admin/me').status_code == 401
