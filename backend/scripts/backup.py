"""Encrypted PostgreSQL backups and isolated restore checks via development Compose."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet


def docker(*args, **kwargs):
    return subprocess.run(["docker", "compose", "exec", "-T", "db", *args], check=True, **kwargs)


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
    cipher = Fernet(args.key_file.read_bytes())
    if not args.file:
        parser.error("--file is required")
    if args.operation == "backup":
        # Temporary cleartext is private and removed on success/failure.
        with tempfile.TemporaryFile() as dump:
            docker("pg_dump", "-U", "prontuario", "-d", "prontuario", "-Fc", stdout=dump)
            dump.seek(0)
            payload = cipher.encrypt(dump.read())
        fd = os.open(args.file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
    else:
        payload = cipher.decrypt(args.file.read_bytes())
        scratch = "restore_check_" + uuid4().hex
        docker("createdb", "-U", "prontuario", scratch)
        try:
            docker("pg_restore", "-U", "prontuario", "-d", scratch, "--exit-on-error", input=payload)
            docker("psql", "-U", "prontuario", "-d", scratch, "-v", "ON_ERROR_STOP=1", "-c",
                   "SELECT 1 FROM alembic_version; SELECT count(*) FROM audit_events; SELECT count(*) FROM record_permissions;")
        finally:
            docker("dropdb", "-U", "prontuario", scratch)
    print("Operation completed; no production database was overwritten.")


if __name__ == "__main__":
    main()
