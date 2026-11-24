# Testes manuais de login no Docker

Modo opcional autorizado, isolado em `prontuario_test_login`. Não executar pytest
nesse banco; a suíte continua usando `prontuario_test`.

Pré-requisitos: Docker com Compose disponível e em execução, Python e dependências
de desenvolvimento instaladas. Os comandos abaixo usam as portas padrão 8001
(API) e 3307 (MySQL).

De `backend`, na primeira execução:

```powershell
python scripts/test_env.py
python scripts/prepare_login_test.py
docker compose -p prontuario-test -f compose.test.yaml -f compose.login-test.yaml up -d --wait backend
```

1. O primeiro comando inicia MySQL, Redis e a API de testes.
2. O segundo prepara o schema separado para os testes manuais de login.
3. O terceiro inicia a API nesse banco e cria `teste` e `admin` automaticamente.

Para conferir, abra o Swagger, clique em **Authorize**, entre com uma das contas
abaixo e selecione seus escopos. Execute `/api/v1/me` e `/api/v1/admin/me` para
comparar as permissões. Use **Logout** no Swagger antes de alternar a conta.

Nas próximas inicializações use apenas o último comando. O override habilita
`TEST_SEED_USERS=1`, aplica migrações técnicas e cria duas fixtures de autenticação.
Contas existentes, senhas alteradas, bloqueios e permissões revogadas são preservados.
Conflitos de identidade são recusados. O preparador recusa banco com tabelas;
se uma importação falhar parcialmente, revise o estado manualmente.

| Login | Senha inicial pública de teste | Escopos |
| --- | --- | --- |
| `teste` | `Teste-Isolado-123` | `identity:read` |
| `admin` | `Admin-Isolado-123` | `identity:read admin:access` |

Senhas ficam como hashes scrypt com salt, não criptografia reversível. A chave
JWT pública do override é exclusiva de testes. Não reutilizar estas credenciais.

- API: `http://127.0.0.1:8001`
- Swagger: `http://127.0.0.1:8001/docs` → **Authorize**.
- Login: `POST /api/v1/auth/token`, `application/x-www-form-urlencoded`.
- Campos: `grant_type=password`, `username`, `password`, `scope`.
- Autenticação: `Authorization: Bearer <access_token>` retornado pelo login.
- `GET /api/v1/me`: 200 para ambos com token válido.
- `GET /api/v1/admin/me`: 200 para admin com ambos os escopos; 403 para teste.
- Login de teste solicitando `admin:access`: 400, escopo não permitido.
- Refresh: `POST /api/v1/auth/refresh`, JSON com `refresh_token` e `scope`.
- Logout: `POST /api/v1/auth/logout` com Bearer, resposta 204.

Não há client ID/client secret. Tokens são gerados no login, não são fixos.
Access token dura 15 minutos; sessão até 7 dias por padrão.
Portas alternativas seguem as variáveis do Compose de testes.
Para voltar ao modo original execute `python scripts/test_env.py`; os bancos são preservados.
