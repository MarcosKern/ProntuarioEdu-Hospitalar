import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


def load_script():
    path = Path(__file__).resolve().parents[2] / "scripts/test_env.py"
    spec = importlib.util.spec_from_file_location("fixed_test_environment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_connection_output_keeps_optional_jwt_secret_private(monkeypatch, capsys):
    script = load_script()
    private_key = "optional-private-signing-key-must-not-be-printed"

    def execute(command, **kwargs):
        if command[1:] == ["ps", "--format", "json"]:
            output = json.dumps(
                [
                    {"Service": name, "State": "running", "Health": "healthy"}
                    for name in ("mysql", "redis", "backend")
                ]
            )
        elif command[1:] == ["config", "--format", "json"]:
            output = json.dumps(
                {
                    "services": {
                        "mysql": {
                            "environment": {
                                "MYSQL_DATABASE": "prontuarioedu",
                                "MYSQL_USER": "prontuario_test",
                                "MYSQL_PASSWORD": "test-only-password",
                                "MYSQL_ROOT_PASSWORD": "test-only-root-password",
                            }
                        },
                        "backend": {"environment": {"AUTH_JWT_SECRET": private_key}},
                    }
                }
            )
        else:
            output = "127.0.0.1:3307" if command[2] == "mysql" else "127.0.0.1:8001"
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(script.subprocess, "run", execute)
    script.show_connections(["docker-stub"], {}, Path.cwd())
    output = capsys.readouterr().out
    assert "MYSQL_PASSWORD=test-only-password" in output
    assert "SWAGGER_URL=http://127.0.0.1:8001/docs" in output
    assert private_key not in output and "AUTH_JWT_SECRET=" not in output


def test_connection_output_is_blocked_until_all_services_are_healthy(
    monkeypatch, capsys
):
    script = load_script()

    def execute(command, **kwargs):
        assert command[1:] == ["ps", "--format", "json"]
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                [{"Service": "backend", "State": "running", "Health": "starting"}]
            ),
            "",
        )

    monkeypatch.setattr(script.subprocess, "run", execute)
    with pytest.raises(ValueError, match="ainda não está saudável"):
        script.show_connections(["docker-stub"], {}, Path.cwd())
    assert capsys.readouterr().out == ""
