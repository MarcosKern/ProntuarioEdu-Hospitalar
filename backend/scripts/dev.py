"""Execute da pasta backend: python scripts/dev.py [--setup]."""

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--setup", action="store_true", help="Criar venv e instalar requirements"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if args.setup:
        if not python.exists():
            venv.EnvBuilder(with_pip=True).create(root / ".venv")
        subprocess.run(
            [str(python), "-m", "pip", "install", "-r", "requirements-dev.txt"],
            check=True,
        )
    if not python.exists():
        parser.error("Ambiente ausente. Execute primeiro com --setup.")
    subprocess.run([str(python), "-m", "alembic", "upgrade", "head"], check=True)
    command = [
        str(python),
        "-m",
        "uvicorn",
        "prontuario_backend.main:app",
        "--app-dir",
        "src",
        "--reload",
        "--no-access-log",
        "--no-proxy-headers",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    try:
        return subprocess.call(command)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
