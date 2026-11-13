import pytest
from pydantic import ValidationError

from prontuario_backend.config.settings import Settings, get_settings


@pytest.mark.parametrize("url", [
    "",
    "mysql+pymysql://",
    "mysql+pymysql://app@mysql/",
    "mysql+pymysql://app@/prontuarioedu",
    "mysql+pymysql://app@mysql:not-a-port/prontuarioedu",
    "mysql+pymysql://app@mysql:0/prontuarioedu",
    "mysql+pymysql://app@mysql:65536/prontuarioedu",
    "mysql+mysqldb://app@mysql/prontuarioedu",
    "sqlite:///unused.db",
])
def test_database_requires_pymysql_and_explicit_server_and_database(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url=url)


def test_database_url_is_required_without_a_fallback(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("url", [
    "mysql+pymysql://app@mysql/prontuarioedu?charset=utf8mb4",
    "mysql+pymysql://app:unit%2Fsecret@db.example.test:3306/prontuarioedu",
])
def test_explicit_mysql_configuration_is_accepted_without_connecting(url):
    settings = Settings(_env_file=None, database_url=url)
    assert settings.database_url.get_secret_value() == url


@pytest.mark.parametrize("query", ["ssl_disabled=true", "READ_TIMEOUT=0"])
def test_url_cannot_override_transport_and_timeout_settings(query):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="mysql+pymysql://app@mysql/prontuarioedu?" + query)


def test_exported_database_url_takes_precedence_over_dotenv(tmp_path, monkeypatch):
    file_url = "mysql+pymysql://app@file-host/file_database"
    exported_url = "mysql+pymysql://app@process-host/process_database"
    config = tmp_path / ".env"
    config.write_text("DATABASE_URL=" + file_url + "\n")
    monkeypatch.setenv("DATABASE_URL", exported_url)
    assert Settings(_env_file=config).database_url.get_secret_value() == exported_url
    monkeypatch.delenv("DATABASE_URL")
    assert Settings(_env_file=config).database_url.get_secret_value() == file_url


def test_configuration_error_does_not_expose_the_connection_password(monkeypatch):
    secret = "isolated-secret-must-not-be-disclosed"
    monkeypatch.setenv("DATABASE_URL", f"mysql+pymysql://app:{secret}@mysql:invalid/prontuarioedu")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="Configuração inválida") as error:
        get_settings()
    assert secret not in str(error.value)
    assert error.value.__suppress_context__ is True


def test_validation_error_hides_raw_connection_input():
    secret = "isolated-secret-must-not-be-disclosed"
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url=f"mysql+pymysql://app:{secret}@mysql/prontuarioedu", allowed_hosts=["*"])
    assert secret not in str(error.value)
