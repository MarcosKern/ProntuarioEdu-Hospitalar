import importlib.util
import json
import ssl
import stat
from pathlib import Path

from cryptography import x509


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
