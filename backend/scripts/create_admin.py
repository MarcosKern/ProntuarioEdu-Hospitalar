"""Cria o administrador local no MySQL configurado, sem salvar ou imprimir sua senha."""
import argparse
import getpass
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prontuario_backend.config.auth import hash_password
from prontuario_backend.config.database import engine
from prontuario_backend.models.users import bootstrap_system_admin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--convert-existing", action="store_true", help="Converter explicitamente o admin externo preservando seu ID e permissões")
    args = parser.parse_args()
    database = engine()
    try:
        with database.connect() as connection:
            account = connection.execute(text("SELECT id, provedor FROM cadastro__usuarios WHERE login='admin'")).mappings().first()
        if account and account["provedor"] != "local" and not args.convert_existing:
            parser.error("Conta externa preservada. Para usar login local, execute com --convert-existing.")
        value = getpass.getpass("Senha do administrador (12 a 128 caracteres): ")
        if value != getpass.getpass("Confirme a senha: "):
            raise ValueError("Senhas diferentes")
        digest = hash_password(value)
        result = bootstrap_system_admin(database, account["id"] if account else str(uuid4()), digest,
                                        convert_existing=args.convert_existing)
        print("Administrador local criado/conversão concluída." if result["created"] or args.convert_existing
              else "Administrador local já existe; senha e permissões preservadas.")
        return 0
    except (ValueError, SQLAlchemyError, EOFError):
        print("Não foi possível criar o administrador. Confira o schema e a conexão configurada; nenhum segredo será exibido.")
        return 1
    finally:
        database.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
