import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text

from prontuario_backend.config.auth import verify_password
from prontuario_backend.models.users import system_admin

spec = importlib.util.spec_from_file_location(
    "seed_test_users", Path(__file__).resolve().parents[2] / "scripts/seed_test_users.py"
)
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


@pytest.mark.parametrize("env,flag,database", [
    ("production", "1", "prontuario_test_login"),
    ("test", "0", "prontuario_test_login"),
    ("test", "1", "prontuarioedu"),
    ("test", "1", "prontuario_test"),
])
def test_fixture_guard_rejects_other_modes(monkeypatch, env, flag, database):
    monkeypatch.setenv("APP_ENV", env)
    monkeypatch.setenv("TEST_SEED_USERS", flag)
    monkeypatch.setenv("DATABASE_URL", f"mysql+pymysql://prontuario_test@mysql/{database}")
    with pytest.raises(ValueError):
        seed.validate_target()


def test_fixture_hashes_permissions_and_restart(application_schema):
    seed.seed_accounts(application_schema)
    with application_schema.connect() as connection:
        assert system_admin(connection, seed.ADMIN_ID)
        assert not system_admin(connection, seed.USER_ID)
        stored = connection.execute(text(
            "SELECT hash_senha FROM cadastro__usuarios WHERE id=:id"
        ), {"id": seed.USER_ID}).scalar_one()
        assert verify_password("Teste-Isolado-123", stored)
    seed.seed_accounts(application_schema)
    with application_schema.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM cadastro__usuarios")).scalar_one() == 2
        assert connection.execute(text(
            "SELECT hash_senha FROM cadastro__usuarios WHERE id=:id"
        ), {"id": seed.USER_ID}).scalar_one() == stored
    with application_schema.begin() as connection:
        connection.execute(text("UPDATE cadastro__usuario_perfil SET revogado_em=UTC_TIMESTAMP(6)"))
    with pytest.raises(ValueError):
        seed.seed_accounts(application_schema)
