"""Prepara o login admin do ProntuarioEdu usando Keycloak e MySQL de desenvolvimento."""
import argparse
import ipaddress
import json
import os
import re
import secrets
import ssl
import string
import subprocess
import textwrap
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from dotenv import dotenv_values, set_key

BACKEND = Path(__file__).resolve().parents[1]


def state_directory(path):
    """Recusa credenciais em áreas versionáveis antes de criar qualquer arquivo."""
    state = path.resolve()
    backend = BACKEND.resolve()
    repository = backend.parent
    internal = state.is_relative_to(repository)
    sensitive = ("compose.env", "realm.json", "admin-inicial.txt", "certs/server.key", "certs/ca.key")
    git_env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        git_env.pop(name, None)
    if internal and not state.is_relative_to(backend / ".local"):
        raise ValueError("Dentro do projeto, use backend/.local/ para o estado privado")
    roots = {}
    for candidate in (state, *(state / name for name in sensitive)):
        resolved = candidate.resolve()
        if not resolved.is_relative_to(state):
            raise ValueError("Arquivos privados não podem apontar para fora do diretório de estado")
        probe = resolved if resolved.is_dir() else resolved.parent
        while not probe.is_dir():
            probe = probe.parent
        if probe not in roots:
            checkout = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=probe,
                                      env=git_env, capture_output=True, text=True, check=False)
            roots[probe] = Path(checkout.stdout.strip()).resolve() if checkout.returncode == 0 else None
        root = roots[probe]
        if root is not None and (not internal or root != repository):
            raise ValueError("Não grave o estado privado dentro de outro repositório Git")
    if internal:
        ignored = all(subprocess.run(["git", "check-ignore", "--quiet", "--", str(state / name)],
                                    cwd=repository, env=git_env, capture_output=True, check=False).returncode == 0
                      for name in sensitive)
        tracked = subprocess.run(["git", "ls-files", "-z", "--", str(state)],
                                 cwd=repository, env=git_env, capture_output=True, check=False)
        if not ignored or tracked.returncode or tracked.stdout:
            raise ValueError("O estado privado deve estar ignorado pelo Git e sem arquivos versionados")
    return state


def private_write(path, value):
    with open(path, "x", opener=lambda name, flags: os.open(name, flags, 0o600)) as output:
        output.write(value)


def password():
    alphabet = string.ascii_letters + string.digits + "-_"
    return "Aa1-" + "".join(secrets.choice(alphabet) for _ in range(36))


def render_realm(state, values):
    target = state / "realm.json"
    if target.exists():
        return

    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, str):
            match = re.fullmatch(r"\$\{([A-Z_]+)\}", value)
            if match:
                return values[match[1]]
            if "${" in value:
                raise ValueError("Marcador de configuração não resolvido no realm")
        return value

    template = json.loads((BACKEND / "docker/keycloak/prontuarioedu-realm.json").read_text())
    private_write(target, json.dumps(replace(template), ensure_ascii=False, indent=2) + "\n")


def certificates(folder, public_host):
    folder.mkdir(mode=0o700)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(UTC)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ProntuarioEdu Development CA")])
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(ca_key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=5))
          .not_valid_after(now + timedelta(days=3650)).add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=False, content_commitment=False,
                                      data_encipherment=False, key_agreement=False, key_cert_sign=True,
                                      crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
          .sign(ca_key, hashes.SHA256()))
    names = [x509.DNSName(n) for n in sorted({"localhost", "keycloak", public_host})]
    names.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
    server = (x509.CertificateBuilder()
              .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]))
              .issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=365))
              .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
              .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
              .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
              .add_extension(x509.SubjectAlternativeName(names), critical=False)
              .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
              .sign(ca_key, hashes.SHA256()))
    for filename, private_key in (("ca.key", ca_key), ("server.key", key)):
        private_write(folder / filename, private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode())
    for filename, cert in (("ca.crt", ca), ("server.crt", server)):
        (folder / filename).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        (folder / filename).chmod(0o644)
    roots = "\n".join(ssl.DER_cert_to_PEM_cert(cert) for cert in ssl.create_default_context().get_ca_certs(binary_form=True))
    (folder / "ca-bundle.crt").write_text(roots + "\n" + ca.public_bytes(serialization.Encoding.PEM).decode())
    (folder / "ca-bundle.crt").chmod(0o644)


def prepare(state, project, https_port, http_port, backend_port):
    state = state_directory(state)
    target = state / "compose.env"
    if target.exists():
        values = dotenv_values(target)
        required = ("AUTH_DB_PASSWORD", "AUTH_DB_ROOT_PASSWORD", "AUTH_MANAGEMENT_PASSWORD", "AUTH_ADMIN_TEMP_PASSWORD",
                    "AUTH_ADMIN_USER_ID", "AUTH_PUBLIC_URL", "AUTH_SWAGGER_ORIGIN", "AUTH_NETWORK_NAME", "AUTH_STATE_DIR")
        if not all(values.get(k) for k in required) or any(not (state / "certs" / n).is_file() for n in ("ca.crt", "server.crt", "server.key", "ca-bundle.crt")):
            raise ValueError("Estado incompleto; não gerar novas credenciais sobre um volume existente")
        if values["AUTH_NETWORK_NAME"] != project:
            raise ValueError("O estado pertence a outro projeto; use seu nome original")
        if Path(values["AUTH_STATE_DIR"]).resolve() != state:
            raise ValueError("O estado pertence a outro diretório; a configuração original foi preservada")
        render_realm(state, values)
        return values
    state.mkdir(parents=True, mode=0o700, exist_ok=True)
    state.chmod(0o700)
    codespace = os.getenv("CODESPACE_NAME", "")
    domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    if codespace and (not re.fullmatch(r"[a-zA-Z0-9-]+", codespace) or not re.fullmatch(r"[a-zA-Z0-9.-]+", domain)):
        raise ValueError("Nome/domínio do Codespace inválido")
    public = f"https://{codespace}-{http_port}.{domain}" if codespace else f"https://localhost:{https_port}"
    swagger = f"https://{codespace}-{backend_port}.{domain}" if codespace else f"http://127.0.0.1:{backend_port}"
    values = {"AUTH_STATE_DIR": str(state), "AUTH_NETWORK_NAME": project, "AUTH_HTTP_PORT": str(http_port),
              "AUTH_HTTPS_PORT": str(https_port), "BACKEND_PORT": str(backend_port), "AUTH_PUBLIC_URL": public, "AUTH_SWAGGER_ORIGIN": swagger,
              "AUTH_SWAGGER_REDIRECT_URI": swagger + "/docs/oauth2-redirect", "AUTH_ADMIN_USER_ID": str(uuid4()),
              "AUTH_DB_PASSWORD": password(), "AUTH_DB_ROOT_PASSWORD": password(), "AUTH_MANAGEMENT_PASSWORD": password(),
              "AUTH_ADMIN_TEMP_PASSWORD": password()}
    certificates(state / "certs", urlsplit(public).hostname)
    private_write(target, "# Configuração privada de desenvolvimento; não versionar.\n")
    for key, value in values.items():
        set_key(target, key, value)
    private_write(state / "admin-inicial.txt", "Usuário do sistema ProntuarioEdu\nLogin: admin\nSenha temporária: "
                  + values["AUTH_ADMIN_TEMP_PASSWORD"] + "\nPerfil: ADMINISTRADOR\n"
                  + "Troca obrigatória no primeiro acesso.\nEsta senha não é do MySQL nem da gestão do provedor.\n")
    render_realm(state, values)
    return values


def configure_api(state, values):
    target = BACKEND / ".env"
    if not target.exists():
        private_write(target, (BACKEND / ".env.example").read_text())
    config = dotenv_values(target)
    if config.get("APP_ENV") == "production":
        raise ValueError("O bootstrap é exclusivo de desenvolvimento; .env de produção preservado")
    configured_hosts = config.get("ALLOWED_HOSTS")
    hosts = json.loads(configured_hosts) if configured_hosts is not None else ["localhost", "127.0.0.1"]
    if not isinstance(hosts, list) or not hosts or any(not isinstance(host, str) or not host or host == "*" for host in hosts):
        raise ValueError("ALLOWED_HOSTS deve conter hosts explícitos em uma lista JSON")
    hostname = urlsplit(values["AUTH_SWAGGER_ORIGIN"]).hostname
    if not hostname:
        raise ValueError("Origem do Swagger inválida")
    if hostname not in hosts:
        hosts.append(hostname)
    realm = values["AUTH_PUBLIC_URL"] + "/realms/prontuarioedu"
    for key, value in {"ALLOWED_HOSTS": json.dumps(hosts), "OIDC_ISSUER": realm, "OIDC_AUDIENCE": "prontuario-api",
                       "OIDC_AUTHORIZATION_URL": realm + "/protocol/openid-connect/auth",
                       "OIDC_TOKEN_URL": realm + "/protocol/openid-connect/token",
                       "OIDC_JWKS_URL": f"https://localhost:{values['AUTH_HTTPS_PORT']}/realms/prontuarioedu/protocol/openid-connect/certs",
                       "OIDC_SSL_CA": str(state / "certs/ca-bundle.crt"), "SWAGGER_CLIENT_ID": "prontuario-swagger"}.items():
        set_key(target, key, value)


def docker_environment():
    env = os.environ.copy()
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
        env.pop(name, None)
    return env


def run(compose, *args):
    subprocess.run([*compose, *args], cwd=BACKEND, env=docker_environment(), check=True)


def bootstrap_app(values, compose):
    # Execute no backend do projeto iniciado: portas/credenciais exportadas não escolhem outro MySQL.
    code = textwrap.dedent("""
        import json
        import sys
        from sqlalchemy.engine import make_url
        from prontuario_backend.config.database import engine
        from prontuario_backend.config.settings import get_settings
        from prontuario_backend.models.users import bootstrap_system_admin

        settings = get_settings()
        target = make_url(settings.database_url.get_secret_value())
        if settings.app_env != 'development' or target.drivername != 'mysql+pymysql' or target.host != 'mysql' or target.database != 'prontuarioedu':
            raise ValueError('Bootstrap restrito ao MySQL do Compose de desenvolvimento')
        database = engine()
        try:
            print(json.dumps(bootstrap_system_admin(database, sys.argv[1])))
        finally:
            database.dispose()
    """)
    completed = subprocess.run([*compose, "exec", "-T", "backend", "python", "-c", code, values["AUTH_ADMIN_USER_ID"]],
                               cwd=BACKEND, env=docker_environment(), capture_output=True, text=True, check=True)
    result = json.loads(completed.stdout)
    print("Administrador da aplicação criado." if result["created"] else "Administrador da aplicação já existe; vínculo preservado.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["setup", "up", "info", "down"], nargs="?", default="up")
    parser.add_argument("--with-backend", action="store_true", help="Iniciar o modo MySQL local, a API e cadastrar o admin na aplicação")
    parser.add_argument("--state-dir", type=Path, default=BACKEND / ".local/auth",
                        help="Dentro do projeto, use somente .local/; diretórios externos devem ficar fora de checkouts Git")
    parser.add_argument("--project-name", default="prontuario-auth")
    parser.add_argument("--https-port", type=int, default=8443)
    parser.add_argument("--http-port", type=int, default=8080)
    parser.add_argument("--backend-port", type=int, default=8000)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", args.project_name) or any(not 1 <= port <= 65535 for port in (args.https_port, args.http_port, args.backend_port)):
        parser.error("Nome de projeto ou porta inválidos")
    state = args.state_dir.resolve()
    try:
        values = prepare(state, args.project_name, args.https_port, args.http_port, args.backend_port)
        compose = ["docker", "--host=unix:///var/run/docker.sock", "compose", "--project-name", args.project_name,
                   "--env-file", str(state / "compose.env"), "-f", str(BACKEND / "compose.auth.yaml")]
        if args.operation == "down":
            run(compose, "down")
            return 0
        if args.operation == "up":
            configure_api(state, values)
            run(compose, "up", "--build", "-d", "--wait", "--wait-timeout", "300")
            if args.with_backend:
                from mysql_dev import prepare as prepare_mysql
                prepare_mysql(BACKEND)
                development = ["docker", "--host=unix:///var/run/docker.sock", "compose", "--project-name", args.project_name + "-app",
                               "--env-file", str(BACKEND / ".env.mysql"), "--env-file", str(state / "compose.env"),
                               "-f", str(BACKEND / "compose.yaml"), "-f", str(BACKEND / "compose.mysql.yaml"),
                               "-f", str(BACKEND / "compose.auth.backend.yaml")]
                run(development, "up", "--build", "-d", "--wait", "--wait-timeout", "180")
                bootstrap_app(values, development)
        print("Login da aplicação: admin; perfil ADMINISTRADOR e permissão USUARIO_GERENCIAR após --with-backend.")
        print("Swagger:", values["AUTH_SWAGGER_ORIGIN"] + "/docs")
        print("Provedor:", values["AUTH_PUBLIC_URL"])
        print("Senha temporária privada (abra localmente):", state / "admin-inicial.txt")
        print("CA pública para confiar no navegador local:", state / "certs/ca.crt")
        print("Setup/info não cadastram usuários no MySQL; up --with-backend executa o bootstrap explícito.")
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError):
        print("Não foi possível preparar o administrador; confira a configuração privada e os logs locais. Nenhuma senha será exibida.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
