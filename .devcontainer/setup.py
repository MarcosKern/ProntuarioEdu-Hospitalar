"""Prepare tools only: never connect to a database or run migrations."""

import argparse
import shutil
import subprocess
import sys
import venv
from pathlib import Path


def prepare(root: Path, install=True):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use Python 3.12, conforme devcontainer.json")
    backend = root / "backend"
    environment = backend / ".env"
    if not environment.exists():
        shutil.copyfile(backend / ".env.example", environment)
        environment.chmod(0o600)
    if not install:
        return
    virtualenv = backend / ".venv"
    python = virtualenv / "bin" / "python"
    if virtualenv.exists() and not python.exists():
        raise RuntimeError(
            "Venv existente inválido; recrie somente backend/.venv antes de continuar"
        )
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(virtualenv)
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-r",
            str(backend / "requirements-dev.txt"),
        ],
        cwd=backend,
        check=True,
    )
    subprocess.run([str(python), "-m", "pip", "check"], cwd=backend, check=True)
    print(
        "Dependências prontas. Configure MySQL e AUTH_JWT_SECRET e use a tarefa Codespaces: iniciar API."
    )
    print("Nenhum SQL foi importado e nenhuma migração foi executada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prepare-config-only",
        action="store_true",
        help="Somente criar .env se ausente",
    )
    args = parser.parse_args()
    prepare(Path(__file__).resolve().parents[1], install=not args.prepare_config_only)
