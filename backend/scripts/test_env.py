"""Start the fixed-credential test stack and show connections only when healthy."""
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def test_environment():
    env = os.environ.copy()
    name = env.get("CODESPACE_NAME", "")
    domain = env.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    port = env.get("BACKEND_TEST_PORT", "8001")
    hosts = ["localhost", "127.0.0.1"]
    if name:
        if not re.fullmatch(r"[a-zA-Z0-9-]+", name) or not re.fullmatch(r"[a-zA-Z0-9.-]+", domain):
            raise ValueError("Nome/domínio do Codespace inválido")
        if not port.isdecimal() or not 1 <= int(port) <= 65535:
            raise ValueError("No Codespace, BACKEND_TEST_PORT precisa ser uma porta fixa de 1 a 65535")
        hosts.append(f"{name}-{port}.{domain}")
    env["TEST_ALLOWED_HOSTS"] = json.dumps(hosts)
    return env


def show_connections(compose, env, backend):
    def read(*args):
        return subprocess.run([*compose, *args], cwd=backend, env=env, check=True,
                              text=True, capture_output=True).stdout.strip()

    status = read("ps", "--format", "json")
    services = json.loads(status) if status.startswith("[") else [json.loads(line) for line in status.splitlines()]
    healthy = {item["Service"] for item in services if item.get("State") == "running" and item.get("Health") == "healthy"}
    if not {"mysql", "redis", "backend"}.issubset(healthy):
        raise ValueError("Ambiente ainda não está saudável; consulte os logs antes de conectar")
    config = json.loads(read("config", "--format", "json"))
    mysql = config["services"]["mysql"]["environment"]
    mysql_port = urlsplit("//" + read("port", "mysql", "3306")).port
    api_port = urlsplit("//" + read("port", "backend", "8000")).port
    prefix = f"mysql+pymysql://{mysql['MYSQL_USER']}:{mysql['MYSQL_PASSWORD']}@127.0.0.1:{mysql_port}/"
    print("\nAmbiente de testes pronto: MySQL, Redis e API saudáveis.")
    print("Credenciais públicas e fixas, exclusivas deste ambiente de testes:")
    values = {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": mysql_port,
        "MYSQL_DATABASE": mysql["MYSQL_DATABASE"],
        "MYSQL_USER": mysql["MYSQL_USER"],
        "MYSQL_PASSWORD": mysql["MYSQL_PASSWORD"],
        "MYSQL_ROOT_PASSWORD": mysql["MYSQL_ROOT_PASSWORD"],
        "DATABASE_URL": prefix + mysql["MYSQL_DATABASE"] + "?charset=utf8mb4",
        "MYSQL_TEST_DATABASE": "prontuario_test",
        "MYSQL_TEST_URL": prefix + "prontuario_test?charset=utf8mb4",
        "MYSQL_TEST_ALLOW_RESET": "prontuario_test",
        "API_URL": f"http://127.0.0.1:{api_port}",
        "SWAGGER_URL": f"http://127.0.0.1:{api_port}/docs",
    }
    for key, value in values.items():
        print(f"{key}={value}")
    if env.get("CODESPACE_NAME"):
        domain = env.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        print(f"SWAGGER_CODESPACE_URL=https://{env['CODESPACE_NAME']}-{api_port}.{domain}/docs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", choices=["up", "info", "down"], default="up")
    parser.add_argument("--no-build", action="store_true", help="Reutilizar imagens de teste já construídas")
    parser.add_argument("--project-name", default="prontuario-test")
    args = parser.parse_args()
    backend = Path(__file__).resolve().parents[1]
    try:
        env = test_environment()
        with tempfile.TemporaryDirectory(prefix="prontuario-test-env-") as temporary:
            # Prevent implicit .env loading; passwords and destinations are fixed in compose.test.yaml.
            empty = Path(temporary) / "empty.env"
            empty.touch()
            compose = ["docker", "compose", "--project-name", args.project_name,
                       "--env-file", str(empty), "-f", str(backend / "compose.test.yaml")]
            if args.operation == "down":
                subprocess.run([*compose, "down"], cwd=backend, env=env, check=True)
                return 0
            if args.operation == "up":
                build = "--no-build" if args.no_build else "--build"
                subprocess.run([*compose, "up", build, "-d", "--wait", "--wait-timeout", "180"],
                               cwd=backend, env=env, check=True)
            show_connections(compose, env, backend)
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            print("Não foi possível concluir o Compose de testes; confira os logs dos serviços.")
        else:
            print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
