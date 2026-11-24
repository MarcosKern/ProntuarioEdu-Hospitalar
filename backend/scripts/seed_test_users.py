"""Fixtures exclusivas de banco descartável para testes manuais de login."""
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from prontuario_backend.config.auth import hash_password
from prontuario_backend.models.users import bootstrap_system_admin

ADMIN_ID = "cf727536-54eb-4818-901b-96f4eab7b72c"
USER_ID = "b0138981-b07a-4b77-ab8e-bc38f46d6bb6"


def validate_target():
    url = make_url(os.environ.get("DATABASE_URL", ""))
    if (os.environ.get("APP_ENV") != "test" or os.environ.get("TEST_SEED_USERS") != "1"
            or url.drivername != "mysql+pymysql" or url.database != "prontuario_test_login"
            or url.host != "mysql" or url.username != "prontuario_test"):
        raise ValueError("Use exclusivamente o Compose de login de teste")
    return url


def seed_accounts(db):
    bootstrap_system_admin(db, ADMIN_ID, hash_password("Admin-Isolado-123"))
    with db.begin() as connection:
        rows = connection.execute(text(
            "SELECT id, login FROM cadastro__usuarios WHERE id=:id OR login='teste' FOR UPDATE"
        ), {"id": USER_ID}).mappings().all()
        if rows:
            if len(rows) != 1 or rows[0]["id"] != USER_ID or rows[0]["login"] != "teste":
                raise ValueError("Conta existente preservada; identidade conflitante")
            return
        connection.execute(text("""
            INSERT INTO cadastro__usuarios (id, nome, login, provedor, hash_senha, senha_alterada_em)
            VALUES (:id, 'Usuário de teste', 'teste', 'local', :hash, UTC_TIMESTAMP(6))
        """), {"id": USER_ID, "hash": hash_password("Teste-Isolado-123")})


def main():
    db = create_engine(validate_target(), hide_parameters=True)
    try:
        seed_accounts(db)
        print("Fixtures de login disponíveis; contas existentes preservadas.")
    finally:
        db.dispose()


if __name__ == "__main__":
    main()
