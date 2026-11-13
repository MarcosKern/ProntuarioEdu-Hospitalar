"""Prepare private credentials for the opt-in MySQL development container."""

import argparse
import os
import secrets
from pathlib import Path
from urllib.parse import quote

from dotenv import dotenv_values, set_key


def prepare(backend: Path):
    base = backend / ".env"
    if not base.exists():
        with open(
            base, "x", opener=lambda path, flags: os.open(path, flags, 0o600)
        ) as output:
            output.write((backend / ".env.example").read_text())
    target = backend / ".env.mysql"
    if target.exists():
        config = dotenv_values(target)
        if not all(
            config.get(key)
            for key in (
                "MYSQL_USER",
                "MYSQL_PASSWORD",
                "MYSQL_ROOT_PASSWORD",
                "DATABASE_URL",
            )
        ):
            raise ValueError(
                ".env.mysql incompleto; revise o arquivo sem trocar senhas de um volume existente"
            )
        print(".env.mysql já existe; configuração e credenciais preservadas.")
        return
    password = secrets.token_urlsafe(32)
    with open(
        target, "x", opener=lambda path, flags: os.open(path, flags, 0o600)
    ) as output:
        output.write(
            "# Credenciais privadas do MySQL de desenvolvimento; não versionar.\n"
        )
    values = {
        "MYSQL_USER": "prontuario_backend",
        "MYSQL_PASSWORD": password,
        "MYSQL_ROOT_PASSWORD": secrets.token_urlsafe(48),
        "MYSQL_PORT": "3306",
        "DATABASE_URL": f"mysql+pymysql://prontuario_backend:{quote(password, safe='')}@mysql:3306/prontuarioedu?charset=utf8mb4",
    }
    for key, value in values.items():
        set_key(target, key, value)
    print(".env.mysql criado com credenciais privadas; .env original preservado.")
    print("Nenhum contêiner iniciado e nenhum banco acessado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        prepare(Path(__file__).resolve().parents[1])
    except ValueError as error:
        parser.exit(1, f"{error}\n")
