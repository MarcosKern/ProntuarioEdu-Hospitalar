"""Run the existing development command with an exact Codespaces forwarded host."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


def forwarded_hosts(hosts, name, domain, port):
    result = list(hosts)
    if name:
        if not re.fullmatch(r"[a-zA-Z0-9-]+", name) or not re.fullmatch(r"[a-zA-Z0-9.-]+", domain):
            raise ValueError("Nome/domínio do Codespaces inválido")
        host = f"{name}-{port}.{domain}"
        if host not in result:
            result.append(host)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Porta inválida")
    root = Path(__file__).resolve().parents[1]
    backend = root / "backend"
    load_dotenv(backend / ".env", override=False)
    hosts = json.loads(os.getenv("ALLOWED_HOSTS", '["localhost","127.0.0.1"]'))
    if not isinstance(hosts, list) or not all(isinstance(host, str) for host in hosts):
        parser.error("ALLOWED_HOSTS deve ser um array JSON de strings")
    hosts = forwarded_hosts(hosts, os.getenv("CODESPACE_NAME", ""),
                            os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev"), args.port)
    os.environ["ALLOWED_HOSTS"] = json.dumps(hosts)
    return subprocess.call([sys.executable, str(backend / "scripts/dev.py"),
                            "--host", "0.0.0.0", "--port", str(args.port)], cwd=backend)


if __name__ == "__main__":
    sys.exit(main())
