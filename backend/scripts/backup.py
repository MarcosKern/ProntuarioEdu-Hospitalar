"""Encrypted backups of the configured external MySQL; isolated restore verification."""

import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sqlalchemy.engine import make_url


def quoted(value):
    return (
        '"'
        + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        + '"'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["keygen", "backup", "verify"])
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--file", type=Path)
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parents[1])
    if args.operation == "keygen":
        fd = os.open(args.key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as key:
            key.write(Fernet.generate_key())
        return
    load_dotenv()
    url = make_url(os.environ["DATABASE_URL"])
    if url.drivername != "mysql+pymysql" or not url.database:
        parser.error("Configure an external MySQL DATABASE_URL")
    cipher = Fernet(args.key_file.read_bytes())
    if not args.file:
        parser.error("--file is required")
    with tempfile.TemporaryDirectory() as directory:
        config = Path(directory) / "mysql.cnf"
        content = (
            "[client]\n"
            + "\n".join(
                f"{key}={quoted(value)}"
                for key, value in {
                    "host": url.host,
                    "port": url.port or 3306,
                    "user": url.username,
                }.items()
            )
            + "\n"
        )
        ca = os.getenv("MYSQL_SSL_CA")
        if os.getenv("APP_ENV") == "production" and not ca:
            parser.error("Production MySQL backup requires MYSQL_SSL_CA")
        if ca:
            content += "ssl-mode=VERIFY_IDENTITY\nssl-ca=/run/mysql-ca.pem\n"
        config.write_text(content)
        config.chmod(0o600)
        docker = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--env",
            "MYSQL_PWD",
            "--mount",
            f"type=bind,src={config},dst=/run/mysql.cnf,readonly",
        ]
        if ca:
            docker += [
                "--mount",
                f"type=bind,src={Path(ca).resolve()},dst=/run/mysql-ca.pem,readonly",
            ]
        if os.getenv("MYSQL_CLIENT_NETWORK"):
            docker += ["--network", os.environ["MYSQL_CLIENT_NETWORK"]]

        def client(program, *params, **kwargs):
            # Encaminhar a senha apenas ao processo filho: não gravar no .cnf
            # nem interpolar seu valor nos argumentos visíveis do Docker.
            client_env = os.environ.copy()
            client_env["MYSQL_PWD"] = url.password or ""
            return subprocess.run(
                docker
                + [
                    "mysql:8.4",
                    program,
                    "--defaults-extra-file=/run/mysql.cnf",
                    *params,
                ],
                check=True,
                env=client_env,
                **kwargs,
            )

        if args.operation == "backup":
            with tempfile.TemporaryFile() as dump:
                client(
                    "mysqldump",
                    "--single-transaction",
                    "--no-tablespaces",
                    "--set-gtid-purged=OFF",
                    url.database,
                    stdout=dump,
                )
                dump.seek(0)
                payload = cipher.encrypt(dump.read())
            fd = os.open(args.file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as output:
                output.write(payload)
        else:
            payload = cipher.decrypt(args.file.read_bytes())
            scratch = "restore_check_" + uuid4().hex
            client("mysql", "-e", f"CREATE DATABASE `{scratch}`")
            try:
                client("mysql", scratch, input=payload)
                client(
                    "mysql",
                    scratch,
                    "-e",
                    "SELECT version_num FROM alembic_version; SELECT count(*) FROM audit_events; SELECT count(*) FROM record_permissions;",
                )
            finally:
                client("mysql", "-e", f"DROP DATABASE `{scratch}`")
    print("Operation completed; configured database was not overwritten.")


if __name__ == "__main__":
    main()
