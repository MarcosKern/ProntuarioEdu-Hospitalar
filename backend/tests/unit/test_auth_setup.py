import importlib.util
import json
import ssl
import stat
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography import x509
from dotenv import dotenv_values
from fastapi.testclient import TestClient

from prontuario_backend.config.settings import get_settings
from prontuario_backend.main import create_app


def load_setup():
    path = Path(__file__).resolve().parents[2] / 'scripts/auth_dev.py'
    spec = importlib.util.spec_from_file_location('auth_development_setup', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_auth_setup_preserves_credentials_and_validates_local_tls(tmp_path, monkeypatch):
    monkeypatch.delenv('CODESPACE_NAME', raising=False)
    setup = load_setup()
    state = tmp_path / 'private-auth'
    first = setup.prepare(state, 'isolated-auth-test', 18443, 18080, 18000)
    second = setup.prepare(state, 'isolated-auth-test', 18443, 18080, 18000)
    assert first == second
    assert stat.S_IMODE((state / 'compose.env').stat().st_mode) == 0o600
    assert stat.S_IMODE((state / 'admin-inicial.txt').stat().st_mode) == 0o600
    assert stat.S_IMODE((state / 'certs/server.key').stat().st_mode) == 0o600
    assert stat.S_IMODE((state / 'realm.json').stat().st_mode) == 0o600
    realm = json.loads((state / 'realm.json').read_text())
    assert realm['users'][0]['id'] == first['AUTH_ADMIN_USER_ID']
    assert realm['users'][0]['credentials'][0]['value'] == first['AUTH_ADMIN_TEMP_PASSWORD']
    assert realm['clients'][0]['redirectUris'] == [first['AUTH_SWAGGER_REDIRECT_URI']]
    assert '${' not in (state / 'realm.json').read_text()
    context = ssl.create_default_context(cafile=str(state / 'certs/ca-bundle.crt'))
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    server = x509.load_pem_x509_certificate((state / 'certs/server.crt').read_bytes())
    names = server.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert {'localhost', 'keycloak'}.issubset(names.get_values_for_type(x509.DNSName))


@pytest.fixture
def private_checkout(tmp_path, monkeypatch):
    setup = load_setup()
    repository = tmp_path / 'checkout'
    backend = repository / 'backend'
    backend.mkdir(parents=True)
    subprocess.run(['git', 'init', '--quiet', str(repository)], check=True, capture_output=True)
    (backend / '.gitignore').write_text('/.local/\n')
    (backend / '.env.example').write_text('APP_ENV=development\nDATABASE_URL=\nALLOWED_HOSTS=["localhost","127.0.0.1"]\n')
    monkeypatch.setattr(setup, 'BACKEND', backend)
    return setup, repository, backend


@pytest.mark.parametrize('relative', ['dev-auth', 'src/private-auth', 'auth-backup'])
def test_private_state_rejects_versionable_paths_before_writing(private_checkout, relative):
    setup, _, backend = private_checkout
    target = backend / relative
    with pytest.raises(ValueError, match=r'backend/\.local/'):
        setup.prepare(target, 'isolated', 18443, 18080, 18000)
    assert not target.exists()


def test_private_state_allows_ignored_alternative_and_refuses_tracked_files(private_checkout):
    setup, repository, backend = private_checkout
    target = backend / '.local/isolated-auth'
    assert setup.state_directory(target) == target
    target.mkdir(parents=True)
    tracked = target / 'existing.txt'
    tracked.write_text('public fixture')
    subprocess.run(['git', '-C', str(repository), 'add', '--force', str(tracked)], check=True, capture_output=True)
    with pytest.raises(ValueError, match='sem arquivos versionados'):
        setup.state_directory(target)


def test_private_state_requires_ignore_and_rejects_symlink_escape(private_checkout):
    setup, _, backend = private_checkout
    target = backend / '.local/isolated-auth'
    (backend / '.gitignore').write_text('')
    with pytest.raises(ValueError, match='ignorado pelo Git'):
        setup.state_directory(target)
    (backend / '.gitignore').write_text('/.local/\n')
    source = backend / 'src'
    source.mkdir()
    (backend / '.local').symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match=r'backend/\.local/'):
        setup.state_directory(target)


def test_private_state_rejects_external_git_checkout(tmp_path):
    setup = load_setup()
    other = tmp_path / 'another-checkout'
    other.mkdir()
    subprocess.run(['git', 'init', '--quiet', str(other)], check=True, capture_output=True)
    target = other / 'private-auth'
    with pytest.raises(ValueError, match='outro repositório'):
        setup.state_directory(target)
    assert not target.exists()


@pytest.mark.parametrize('nested', ['state', 'certificates'])
def test_private_state_rejects_nested_git_checkout(private_checkout, nested):
    setup, _, backend = private_checkout
    state = backend / '.local/private-auth'
    checkout = state if nested == 'state' else state / 'certs'
    checkout.mkdir(parents=True)
    subprocess.run(['git', 'init', '--quiet', str(checkout)], check=True, capture_output=True)
    with pytest.raises(ValueError, match='outro repositório'):
        setup.prepare(state, 'isolated', 18443, 18080, 18000)
    assert not (state / 'compose.env').exists()
    assert not (state / 'realm.json').exists()


def test_private_state_rejects_sensitive_symlink_escape(private_checkout, tmp_path):
    setup, _, backend = private_checkout
    state = backend / '.local/private-auth'
    state.mkdir(parents=True)
    (state / 'certs').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='fora do diretório'):
        setup.state_directory(state)


@pytest.mark.parametrize('port', ['13306', '31876'])
def test_bootstrap_uses_running_backend_instead_of_host_mysql_settings(monkeypatch, port):
    setup = load_setup()
    compose = ['docker', 'compose', '--project-name', 'isolated-regression-app']
    subject = str(uuid4())
    calls = []
    monkeypatch.setenv('MYSQL_PORT', port)

    def no_credentials_file(*args, **kwargs):
        pytest.fail('Bootstrap must use the running backend connection, not .env.mysql')

    def execute(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, json.dumps({'created': False, 'user_id': subject, 'login': 'admin'}), '')

    monkeypatch.setattr(setup, 'dotenv_values', no_credentials_file)
    monkeypatch.setattr(setup.subprocess, 'run', execute)
    setup.bootstrap_app({'AUTH_ADMIN_USER_ID': subject}, compose)
    assert len(calls) == 1
    command, options = calls[0]
    assert command[:len(compose)] == compose
    assert command[len(compose):len(compose) + 5] == ['exec', '-T', 'backend', 'python', '-c']
    assert command[-1] == subject
    assert options['env']['MYSQL_PORT'] == port


def test_codespaces_configuration_preserves_hosts_and_allows_forwarded_swagger(private_checkout, monkeypatch):
    setup, _, backend = private_checkout
    env_file = backend / '.env'
    env_file.write_text('APP_ENV=development\nDATABASE_URL=\nALLOWED_HOSTS=["localhost","127.0.0.1","existing.example.test"]\n')
    name = 'review-codespace-18000.app.github.dev'
    values = {'AUTH_PUBLIC_URL': 'https://review-codespace-18080.app.github.dev',
              'AUTH_SWAGGER_ORIGIN': 'https://' + name, 'AUTH_HTTPS_PORT': '18443'}
    setup.configure_api(backend / '.local/isolated-auth', values)
    first = dotenv_values(env_file)
    setup.configure_api(backend / '.local/isolated-auth', values)
    hosts = json.loads(dotenv_values(env_file)['ALLOWED_HOSTS'])
    assert hosts == ['localhost', '127.0.0.1', 'existing.example.test', name]
    assert dotenv_values(env_file) == first
    monkeypatch.setenv('ALLOWED_HOSTS', json.dumps(hosts))
    get_settings.cache_clear()
    with TestClient(create_app(), base_url='https://' + name) as client:
        assert client.get('/docs').status_code == 200
        assert client.get('/openapi.json').status_code == 200
        assert client.get('/docs', headers={'host': 'untrusted.example.test'}).status_code == 400


def test_invalid_existing_hosts_are_preserved_without_partial_config(private_checkout):
    setup, _, backend = private_checkout
    env_file = backend / '.env'
    original = 'APP_ENV=development\nALLOWED_HOSTS=["*"]\n'
    env_file.write_text(original)
    values = {'AUTH_PUBLIC_URL': 'https://localhost:18443', 'AUTH_SWAGGER_ORIGIN': 'http://127.0.0.1:18000', 'AUTH_HTTPS_PORT': '18443'}
    with pytest.raises(ValueError, match='hosts explícitos'):
        setup.configure_api(backend / '.local/auth', values)
    assert env_file.read_text() == original
