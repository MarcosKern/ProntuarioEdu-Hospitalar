"""Prepara schema vazio de testes manuais no Compose de testes existente."""
import subprocess
from pathlib import Path


def main():
    backend = Path(__file__).resolve().parents[1]
    source = (backend / "docs/database/prontuarioedu_mysql.sql").read_text(encoding="utf-8")
    # O DDL contém CREATE DATABASE e USE explícitos; mudar ambos, nunca o arquivo original.
    source = source.replace("`prontuarioedu`", "`prontuario_test_login`")
    source += "\nGRANT ALL PRIVILEGES ON `prontuario_test_login`.* TO 'prontuario_test'@'%';\n"
    compose = ["docker", "compose", "-p", "prontuario-test", "-f", "compose.test.yaml"]
    query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='prontuario_test_login'"
    result = subprocess.run([*compose, "exec", "-T", "mysql", "sh", "-c",
                             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -u root -N -e "' + query + '"'],
                            cwd=backend, check=True, capture_output=True, text=True)
    if result.stdout.strip() != "0":
        raise SystemExit("Banco já contém tabelas; preservado. Use o override para iniciar a API.")
    subprocess.run([*compose, "exec", "-T", "mysql", "sh", "-c",
                    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -u root'],
                   cwd=backend, check=True, input=source.encode("utf-8"))
    print("Schema de testes manuais preparado, sem contas ou dados clínicos.")


if __name__ == "__main__":
    main()
