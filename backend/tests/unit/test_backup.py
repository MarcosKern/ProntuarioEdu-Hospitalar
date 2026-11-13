"""A senha de backup não deve aparecer em arquivos ou argumentos do Docker."""

import importlib.util
from pathlib import Path

from cryptography.fernet import Fernet


def test_backup_keeps_password_out_of_files_and_command(monkeypatch, tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/backup.py"
    spec = importlib.util.spec_from_file_location("backup_script", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    password = "isolated-backup-password-not-for-storage"
    monkeypatch.setenv(
        "DATABASE_URL", f"mysql+pymysql://backup:{password}@db.example/prontuarioedu"
    )
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("MYSQL_SSL_CA", raising=False)
    monkeypatch.delenv("MYSQL_PWD", raising=False)
    monkeypatch.setattr(module, "load_dotenv", lambda: None)
    key = Fernet.generate_key()
    key_file = tmp_path / "key"
    key_file.write_bytes(key)
    output = tmp_path / "backup.enc"
    monkeypatch.setattr(
        "sys.argv",
        [str(script), "backup", "--key-file", str(key_file), "--file", str(output)],
    )
    calls = []

    def run(command, **kwargs):
        assert password not in " ".join(command)
        assert kwargs["env"]["MYSQL_PWD"] == password
        assert command[command.index("--env") + 1] == "MYSQL_PWD"
        mount = next(arg for arg in command if "dst=/run/mysql.cnf" in arg)
        config = Path(mount.split("src=", 1)[1].split(",", 1)[0])
        assert password not in config.read_text()
        assert "password=" not in config.read_text()
        kwargs["stdout"].write(b"-- isolated dump\n")
        calls.append(command)

    monkeypatch.setattr(module.subprocess, "run", run)
    module.main()
    assert len(calls) == 1
    assert Fernet(key).decrypt(output.read_bytes()) == b"-- isolated dump\n"
    assert "MYSQL_PWD" not in module.os.environ
