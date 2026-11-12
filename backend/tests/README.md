# Testar o Back-end

Para subir o ambiente com **MySQL, Redis, API e credenciais fixas exibidas no terminal**, consulte o [Compose exclusivo de testes](../docker/mysql/TESTING.md). De `backend`, execute `python3 scripts/test_env.py`. O banco `prontuario_test` é separado do banco `prontuarioedu` da API.

Execute de `backend`, com o venv já preparado e as dependências de `requirements-dev.txt` instaladas. Os comandos são os mesmos da CI:

```bash
python -m ruff check src tests scripts
python -m pip check
python -m pytest -q
python -m pip_audit -r requirements.txt
python -m pip_audit -r requirements-dev.txt
```

No PowerShell sem ativação, use `.\.venv\Scripts\python.exe` no lugar de `python`.

## Testes com MySQL

Os testes de integração precisam de `MYSQL_TEST_URL` e `MYSQL_TEST_ALLOW_RESET` no **ambiente do processo**. O banco deve ser exclusivo de testes, descartável, com nome iniciado por `prontuario_test` e permissão para criar/apagar tabelas e triggers. O servidor pode ser o mesmo do desenvolvimento se houver autorização do responsável, mas o banco deve ser diferente.

**Confirmação obrigatória:** `MYSQL_TEST_ALLOW_RESET` deve ser exatamente o nome do banco de teste (por exemplo, `prontuario_test`). Sem essa confirmação, a suíte recusa qualquer limpeza. A conexão também não pode apontar ao mesmo host/porta/banco de `DATABASE_URL` da aplicação, mesmo com outro usuário; localhost e loopback são tratados como o mesmo host.

**A fixture apaga `audit_events`, `record_permissions` e `alembic_version` antes de cada teste quando MYSQL_TEST_URL está definida. Nunca use uma URL do banco de aplicação.** Não executar a suíte em paralelo contra o mesmo banco.

Uma forma de fornecer a variável sem colocá-la no histórico é criar privadamente `backend/.env.test` contendo `MYSQL_TEST_URL` com sua conexão de teste e `MYSQL_TEST_ALLOW_RESET` com o nome exato desse banco. Esse arquivo já é ignorado. Rode então:

```bash
python -m dotenv -f .env.test run -- python -m pytest -q
```

No PowerShell sem ativação do venv, use os dois caminhos explicitamente:

```powershell
.\.venv\Scripts\python.exe -m dotenv -f .env.test run -- .\.venv\Scripts\python.exe -m pytest -q
```

A CLI dotenv já está disponível pelas dependências instaladas. Nunca atribua a conexão de teste a `DATABASE_URL` da aplicação. A fixture a substitui internamente após validar os destinos. Nomes DNS diferentes podem apontar ao mesmo servidor: mantenha os nomes do ambiente consistentes e confirme o isolamento com o operador.

O arquivo `.env.test` não é carregado automaticamente por pytest; o comando acima injeta sua variável no processo. Se o servidor exigir CA, configure `MYSQL_SSL_CA` correspondente; a verificação de TLS não deve ser desativada. Variáveis já exportadas e o `.env` também podem afetar settings: mantenha a configuração de teste separada e revise os destinos privadamente.

Sem MYSQL_TEST_URL, testes dependentes de banco são **pulados**, não aprovados. A CI fornece MySQL exclusivo do runner e executa esses testes. Os dados transitórios usados na suíte não são carregados na aplicação; não há seed de usuários ou prontuários.

## Organização e cobertura atual

| Arquivo/pasta | Verificação |
| --- | --- |
| `integration/test_development.py` | Saúde com SQL, Swagger/OpenAPI e tokens assinados em teste |
| `integration/test_authentication.py` | Validação antes do endpoint, claims e assinatura JWT, escopos, JWKS, expiração e recomendação de renovação |
| `integration/test_admin.py` | Cadastro inicial da aplicação, idempotência, recusa de takeover e bloqueio por desativação/revogação |
| `unit/test_auth_setup.py` | Estado privado persistente, renderização correta do realm e confiança TLS |
| `integration/test_security.py` | Configuração, limites, headers, CORS, migrações e autorização/auditoria |
| `integration/test_mysql.py` | Migrações MySQL e proteção de auditoria contra exclusão |
| `unit/` | Reservado para testes unitários adicionais |
| `contract/` | Reservado para cobertura completa de contratos futuros |

Os testes OIDC usam chaves isoladas; não comprovam login/logout no provedor externo. Os testes existentes também não representam cobertura de funcionalidades clínicas ainda não implementadas. Consulte [MYSQL.md](../MYSQL.md#testes) e [SECURITY.md](../SECURITY.md).

A suíte operacional também verifica os timeouts enviados ao driver SQL, os schemas OpenAPI das respostas de erro e a ausência de valores sensíveis em diagnósticos de falhas internas.
