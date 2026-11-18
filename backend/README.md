# Subir o backend com Docker e abrir o Swagger

Este é o roteiro principal de execução. Ao final, você terá **API, MySQL 8.4 e Redis** em contêineres, um administrador da aplicação e o Swagger acessível. Os comandos usam Bash em Linux, macOS, WSL2 ou no terminal do GitHub Codespaces.

O caminho abaixo escolhe explicitamente o MySQL de desenvolvimento em contêiner. O Compose base continua usando MySQL externo; se você já recebeu uma conexão do responsável, use a [alternativa com banco externo](#usar-mysql-externo) em vez de iniciar outro banco.

## 1. Preparar as ferramentas

No computador, instale [Git](https://git-scm.com/downloads), Python **3.12** e [Docker Desktop](https://docs.docker.com/desktop/) ou [Docker Engine com Compose](https://docs.docker.com/engine/install/). No Windows, use o terminal WSL2 com a integração do Docker Desktop habilitada. Mantenha o Docker em execução.

No GitHub Codespaces, primeiro conclua a [preparação do editor](../.devcontainer/README.md). Ela já instala as ferramentas e prepara o venv; não inicia os serviços.

Clone o repositório se ainda não tem um checkout, selecione a branch com a implementação desejada e entre em `backend`:

```bash
git clone https://github.com/MarcosKern/ProntuarioEdu-Hospitalar.git
cd ProntuarioEdu-Hospitalar/backend
```

Se já abriu o projeto, apenas entre em `backend` a partir da raiz. **Todos os comandos restantes deste guia partem dessa pasta.**

Confira o Docker e o Compose (2.24 ou posterior):

```bash
docker info
docker compose version
```

Fora do Codespace, prepare o Python usado pelos scripts e testes:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
```

Confirme que `python3 --version` é 3.12 antes de criar o venv. No Codespace, basta conferir `.venv/bin/python --version` e `.venv/bin/python -m pip check`; não reinstale em paralelo ao setup automático.

## 2. Preparar a configuração privada

```bash
.venv/bin/python scripts/mysql_dev.py
```

Esse comando cria `.env` se estiver ausente e gera `.env.mysql` com credenciais privadas para o MySQL. Se já existem, preserva as configurações. Não inicia contêineres nem acessa banco.

Crie a chave JWT no `.env` sem imprimi-la. O bloco abaixo preserva uma chave já configurada:

```bash
.venv/bin/python - <<'PY'
import secrets
from dotenv import dotenv_values, set_key

if not dotenv_values('.env').get('AUTH_JWT_SECRET'):
    set_key('.env', 'AUTH_JWT_SECRET', secrets.token_urlsafe(48))
print('Chave JWT pronta.')
PY
chmod 600 .env .env.mysql
```

Mantenha `APP_ENV=development` no `.env` para habilitar o Swagger. Não precisa preencher `DATABASE_URL` com servidor externo neste modo: o override fornece o destino interno `mysql:3306`. `AUTH_JWT_SECRET`, `ALLOWED_HOSTS` e CORS vêm de `.env`; as credenciais SQL vêm de `.env.mysql`. Nenhum desses arquivos deve ir para o Git. Este roteiro usa a porta HTTP 8000 (`BACKEND_PORT` ausente ou 8000 em `.env.mysql`). Se preservar outra porta de uma instalação existente, adapte as URLs e o hostname permitido.

### Ajuste adicional somente no Codespace

O navegador usa um hostname do GitHub. Gere a linha com o host exato da porta 8000:

```bash
.venv/bin/python - <<'PY'
import json
import os

name = os.environ['CODESPACE_NAME']
domain = os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')
print('ALLOWED_HOSTS=' + json.dumps(['localhost', '127.0.0.1', f'{name}-8000.{domain}']))
PY
```

Substitua a linha `ALLOWED_HOSTS` no `.env` pela linha gerada. Preserve outros hosts aprovados se houver. Não use `*`. Esse ajuste é do serviço Compose, não da configuração do editor.

## 3. Construir e iniciar os serviços

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml config --quiet
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml up --build -d --wait
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml ps
```

O primeiro comando valida sem imprimir segredos. O segundo constrói as imagens e espera a saúde dos serviços. `-d` mantém os contêineres em segundo plano; não precisa deixar o terminal aberto. O primeiro build pode demorar e exige acesso ao registry Docker, PyPI e repositórios Alpine.

O MySQL importa o SQL inicial **somente se seu volume estiver vazio**. Depois, a API aplica as migrations técnicas Alembic e inicia. Nenhum cadastro é inserido automaticamente. Se a migração falhar, a API não inicia; consulte os logs na seção de diagnóstico.

Confira a consulta SQL de saúde:

```bash
curl --fail --show-error http://127.0.0.1:8000/health
```

Resultado esperado: `{"status":"ok","database":"ok"}`. Isso confirma acesso SQL, mas ainda não comprova o login.

## 4. Criar o administrador da aplicação

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml exec backend python scripts/create_admin.py
```

Digite uma senha de **12 a 128 caracteres**, duas vezes no prompt. Ela não aparece no terminal. O usuário criado é **`admin` do ProntuarioEdu**, não o usuário técnico de conexão ao MySQL. Não existe senha padrão.

Repetir o comando preserva a senha e as permissões existentes; não redefine a conta. Para converter uma conta externa antiga, consulte [autenticação](docs/AUTENTICACAO.md#administrador-existente).

## 5. Abrir e usar o Swagger

No computador, abra **http://127.0.0.1:8000/docs**.

No Codespace, abra a aba **Ports**, encaminhe a porta **8000** e mantenha a visibilidade **Private**. Use **Open in Browser** e acrescente `/docs` ao endereço encaminhado. O login do GitHub no túnel é separado do login da aplicação. Não encaminhe a porta MySQL publicamente.

No Swagger, clique em **Authorize** e escolha **uma** alternativa:

- **OAuth2PasswordBearer:** informe `admin` e a senha criada, marque `identity:read` e `admin:access` e confirme. Deixe client ID/client secret vazios.
- **BearerToken:** se já tem um `access_token`, cole somente seu valor, sem o prefixo `Bearer`, e confirme. Não use o refresh token nesse campo.

Feche o modal e execute **GET `/api/v1/admin/me` → Try it out → Execute**. Espere HTTP **200**. O Swagger envia o header Bearer automaticamente; não há um campo de token em cada operação. Para trocar de alternativa, limpe a autorização anterior no modal.

| Endereço | Finalidade |
| --- | --- |
| `/health` | Saúde pública da API e do MySQL |
| `/docs` | Interface Swagger |
| `/openapi.json` | Contrato para clientes e Postman |
| `/api/v1/me` | Identidade autenticada, com escopo `identity:read` |
| `/api/v1/admin/me` | Identidade administrativa, com os dois escopos e concessão ativa |

**Try it out faz requisições reais.** Para encerrar a sessão no servidor, execute `POST /api/v1/auth/logout` antes de usar Logout no modal; espere 204. O Logout do modal apenas limpa o token da página. A autorização não persiste ao recarregar a página. O [contrato de autenticação](docs/AUTENTICACAO.md) explica renovação, senha e validade da sessão.

## 6. Parar, voltar e atualizar

Use sempre os mesmos arquivos Compose e o mesmo nome de projeto, caso tenha informado `--project-name`:

```bash
# Parar os serviços, preservando o banco no volume.
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml down
# Voltar sem reconstruir imagens.
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml up -d --wait
# Aplicar alterações de código, dependências ou configuração.
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml up --build -d --wait
```

Não use `down -v` para uma instalação com dados que precisa preservar. Alterar `.env.mysql` não troca a senha já armazenada no MySQL. Migrations futuras atualizam volumes existentes; reconstruir a imagem não reaplica o SQL inicial.

## Diagnosticar falhas

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml ps
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml logs --tail=100 backend mysql redis
```

| Sintoma | O que verificar |
| --- | --- |
| Docker indisponível | Docker Desktop/Engine ativo; log de criação do Codespace, se aplicável |
| Porta ocupada | Ajuste `MYSQL_PORT` ou `BACKEND_PORT` em `.env.mysql`; não pare serviços de outra pessoa. Adapte URL e hostname permitido se mudar a porta HTTP |
| Build retorna 403 ou falha de download | Acesso ao registry, PyPI ou domínio Alpine indicado no erro; liberação de rede. Não desative TLS |
| Erro de certificado no build | Bundle de CA do proxy; veja [build com proxy](#build-com-proxy) |
| MySQL/API não saudável | Logs, primeiro import do SQL, privilégios de migration e credenciais correspondentes ao volume |
| `400 Invalid host header` | Host exato em `ALLOWED_HOSTS` no `.env`; recrie a API após corrigir |
| Login retorna 503 | Chave JWT configurada, conexão SQL e tabelas de autenticação disponíveis |
| Chamada protegida retorna 401 | Login/token/sessão válidos; sem token, 401 é esperado |
| Chamada administrativa retorna 403 | Token com ambos os escopos e concessão administrativa ativa |

Antes de compartilhar logs, remova URLs de conexão, tokens e senhas.

### Build com proxy

Se sua rede exige CA corporativa, use um bundle confiável do host. Exemplo Linux:

```bash
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t prontuario-backend-dev .
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml build mysql
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml up -d --no-build --wait
```

Adapte o caminho ao seu sistema. O segredo é usado só no build; não configura o certificado do MySQL. Não repita `up --build` nesse fluxo sem fornecer o segredo novamente. HTTP 403 exige corrigir a permissão de rede; a CA resolve confiança TLS, não autorização.

## Usar MySQL externo

Esta alternativa substitui os passos de preparação SQL e inicialização do modo local; não execute os dois stacks na mesma porta. Prepare `.env` conforme [conexão e TLS MySQL](docs/MYSQL.md), incluindo `DATABASE_URL`, chave JWT e hostname permitido. O operador deve instalar o schema de domínio autorizado antes do cadastro de usuários; Alembic sozinho não cria suas 64 tabelas.

Sem CA privada no contêiner:

```bash
docker compose config --quiet
docker compose up --build -d --wait
docker compose exec backend python scripts/create_admin.py
```

Se o servidor exigir CA fornecida pelo operador, use o [override TLS](docs/MYSQL.md#certificado-mysql-no-compose) em todos os comandos. Neste modo, `DATABASE_URL` do terminal tem precedência na interpolação; os demais campos da aplicação vêm do `.env` via `env_file`. Um segredo exportado no Codespace não é automaticamente encaminhado a todo campo do serviço.

Depois da subida, continue no [passo 5](#5-abrir-e-usar-o-swagger). Para logs, parada e atualização, use `docker compose` sem os arquivos do modo MySQL local, ou mantenha o override TLS se o tiver escolhido.

## Próximos passos

- [Desenvolver pelo Python e manter as dependências](docs/DESENVOLVIMENTO.md).
- [Executar testes em banco descartável](tests/README.md): o Compose de testes é para automação/diagnóstico, não outro roteiro de primeiro acesso.
- [Entender MVC e a organização do código](../docs/architecture.md).
- [Hospedar em servidor e preparar produção](../infra/README.md): o Compose deste guia é de desenvolvimento.
