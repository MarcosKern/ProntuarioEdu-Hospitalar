# Testes do backend

Este é o guia da suíte automatizada. Para **subir a aplicação e abrir o Swagger pela primeira vez**, siga o [roteiro principal](../README.md); o stack de credenciais fixas abaixo é uma ferramenta de testes, não um segundo onboarding.

Use o venv de Python 3.12 com `requirements-dev.txt`, preparado no roteiro principal. Todos os comandos deste documento partem de **`backend`**. Dados transitórios da suíte ficam no banco descartável, nunca em bancos de aplicação.

## Verificações sem MySQL

```bash
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m pip check
env MYSQL_TEST_URL= MYSQL_TEST_ALLOW_RESET= .venv/bin/python -m pytest -q tests/unit tests/contract
```

Os testes unitários usam substitutos e as rotas de contrato são executadas em memória. Essa seleção não comprova integração SQL. Na suíte completa, testes dependentes de MySQL sem `MYSQL_TEST_URL` são **pulados**, não aprovados.

## Suíte completa com MySQL descartável

### 1. Iniciar o stack exclusivo de testes

```bash
.venv/bin/python scripts/test_env.py
```

O script usa `compose.test.yaml`, constrói as imagens, inicia MySQL + Redis + API e espera todos ficarem saudáveis. Não carrega `.env` ou `.env.mysql` implicitamente. Só depois da saúde imprime as conexões públicas de teste; falha de build/saúde não é tratada como sucesso.

| Destino padrão | Valor |
| --- | --- |
| MySQL no host/Codespace | `127.0.0.1:3307` |
| Usuário / senha SQL de teste | `prontuario_test` / `test-only-password` |
| Senha root de teste | `test-only-root-password`, não enviada à API |
| Database da API de teste | `prontuarioedu` |
| Database descartável da suíte | `prontuario_test` |
| API / Swagger de teste | `http://127.0.0.1:8001` / `http://127.0.0.1:8001/docs` |

As credenciais são intencionalmente versionadas para esse stack isolado, com portas em loopback. O MySQL inicializa o DDL em volume vazio e cria o segundo database via `docker/mysql/20-test-database.sql`; a API aplica Alembic somente em `prontuarioedu`. A suíte apaga suas tabelas técnicas em **`prontuario_test`**, separado da API.

### 2. Configurar o destino da suíte

Crie privadamente `backend/.env.test`, já ignorado pelo Git. Para as portas padrão acima, seu conteúdo é:

```dotenv
MYSQL_TEST_URL=mysql+pymysql://prontuario_test:test-only-password@127.0.0.1:3307/prontuario_test?charset=utf8mb4
MYSQL_TEST_ALLOW_RESET=prontuario_test
```

```bash
chmod 600 .env.test
APP_ENV=test MYSQL_SSL_CA='' .venv/bin/python -m dotenv -f .env.test run -- .venv/bin/python -m pytest -q
```

O `dotenv run` injeta as variáveis no processo: pytest não lê `.env.test` sozinho. Use `MYSQL_SSL_CA=''` somente para esse MySQL local de testes; servidor externo com TLS exige sua CA confiável.

**O reset apaga `audit_events`, `record_permissions` e `alembic_version` antes dos casos.** A confirmação deve ser exatamente o nome do banco descartável, com padrão `prontuario_test` ou `prontuario_test_…`. A suíte recusa driver diferente, banco de aplicação, destino coincidente e confirmação ausente. Não execute testes em paralelo contra o mesmo database.

Se usar outro servidor de teste autorizado, substitua a URL por sua conexão privada e ajuste a confirmação. Ele precisa permitir criação/exclusão de tabelas e triggers. Não coloque essa conexão em `DATABASE_URL` da aplicação: a fixture valida os destinos antes de substituir internamente os settings. Nomes DNS distintos podem apontar para o mesmo servidor; confirme o isolamento com o operador.

### 3. Auditar e encerrar

```bash
.venv/bin/python -m pip_audit -r requirements.txt
.venv/bin/python -m pip_audit -r requirements-dev.txt
.venv/bin/python scripts/test_env.py info
.venv/bin/python scripts/test_env.py down
```

A auditoria consulta o índice de pacotes e não substitui o scan da imagem. `info` só imprime conexões com os três serviços saudáveis. `down` preserva o volume do stack; não remove volumes de desenvolvimento.

## Opções do stack de testes

- **Imagens já atualizadas:** `scripts/test_env.py --no-build` reutiliza imagens; não o use para testar código que ainda não entrou nelas.
- **Portas ocupadas:** forneça `MYSQL_TEST_PORT` e `BACKEND_TEST_PORT` no ambiente do processo; use as conexões realmente impressas.
- **Projetos simultâneos:** `--project-name` distingue volumes e serviços; repita o mesmo nome em `up`, `info`, `down` e comandos `docker compose` desse projeto. Cada stack precisa de portas próprias.
- **Codespaces:** encaminhe a porta HTTP 8001 como **Private** e use `SWAGGER_CODESPACE_URL` exibida pelo script. O script calcula o hostname permitido; não publica MySQL para o navegador.
- **Proxy com CA no build:** siga o [fluxo de proxy](../README.md#build-com-proxy), usando `prontuario-backend-test` como tag da API; construa o MySQL com `docker compose -f compose.test.yaml build mysql` e inicie o script com `--no-build`.

### Login manual nesse stack

Por padrão não há chave JWT, usuário ou senha administrativa da aplicação: saúde/docs funcionam, mas login retorna 503. Credenciais SQL não autenticam usuários do ProntuarioEdu.

Se precisar testar o login pela interface, acrescente uma chave `AUTH_JWT_SECRET` exclusiva ao `.env.test` (gere-a localmente, sem copiar a chave de produção) e inicie o script por esse processo:

```bash
.venv/bin/python -m dotenv -f .env.test run -- .venv/bin/python scripts/test_env.py
docker compose --project-name prontuario-test --env-file .env.test -f compose.test.yaml exec backend python scripts/create_admin.py
```

A chave é encaminhada explicitamente e não aparece na saída das conexões. O cadastro usa o database `prontuarioedu` do contêiner, não `MYSQL_TEST_URL`. Substitua o nome do projeto se escolheu outro. A partir daí, use as mesmas instruções de [Authorize](../README.md#5-abrir-e-usar-o-swagger), na porta **8001**. Alterar a chave exige recriar a API com o mesmo comando de inicialização.

## Organização e cobertura

| Pasta | Responsabilidade e principais cenários |
| --- | --- |
| `unit/` | Configuração, startup sem SQL/seeds, DTOs, paginação, privacidade da saída do stack e senha fora de arquivo/argumentos do backup |
| `contract/` | Swagger/OAuth2/Bearer, operações OpenAPI, escopos, schemas, erros HTTP, limites, headers e exportação |
| `integration/` | Login/sessões reais, administrador e concessões, saúde, falha/timeout SQL, transações/rollback, migrations, collation, auditoria e segurança HTTP |

Rotas temporárias de paginação/erro dos testes não são endpoints da aplicação. Fixtures não carregam pacientes ou contas de demonstração no projeto. Detalhes dos testes são os próprios `test_*.py`, evitando inventários duplicados em cada subpasta.

A [CI](../../.github/workflows/backend.yml) executa lint, `pip check`, pytest com MySQL exclusivo e os dois locks auditados; o job `image` constrói e analisa a imagem com Trivy. [CodeQL](../../.github/workflows/codeql.yml) verifica Python separadamente. Confira os resultados no commit do PR, não em contagens históricas.
