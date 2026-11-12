# MySQL de desenvolvimento com o schema pronto

Este modo opcional cria um **MySQL 8.4 em contêiner**, inicializa o SQL recebido e conecta a API ao banco `prontuarioedu`. É destinado a desenvolvimento local ou no Codespace. O [Compose base](../../compose.yaml) continua sendo o caminho de conexão a MySQL externo.

O MySQL roda em um serviço próprio. A imagem do banco contém o SQL em `/docker-entrypoint-initdb.d/10-prontuarioedu.sql`; a imagem da API continua separada. Não há cadastros, contas da aplicação ou pacientes de demonstração.

Para **testes com variáveis fixas e conexão exibida automaticamente no terminal**, use o [Compose exclusivo de testes](TESTING.md): `python3 scripts/test_env.py`, executado de `backend`. O roteiro abaixo trata do modo de desenvolvimento com credenciais privadas geradas.

## 1. Preparar os arquivos privados

Com Docker/Compose funcionando e o venv de desenvolvimento instalado, entre em `backend` e execute:

```bash
.venv/bin/python scripts/mysql_dev.py
```

O script cria `.env` a partir do exemplo apenas se ainda não existir. Depois gera `.env.mysql`, com usuário técnico de desenvolvimento, senha forte, senha root distinta e URL de conexão. O arquivo tem permissão `0600`, é ignorado pelo Git e excluído do contexto de build. As credenciais não são impressas.

O `.env` original é preservado. Repetir o script mantém as credenciais de `.env.mysql`, para continuar acessando um volume já inicializado. Não é necessário preencher uma URL de banco externo para esse modo.

Configurações da aplicação, como `ALLOWED_HOSTS`, CORS e AUTH_JWT_SECRET, continuam no `.env`. O arquivo `.env.mysql` fornece apenas os parâmetros do banco/Compose; a senha root é enviada somente ao serviço MySQL. O serviço da API recebe uma URL com destino interno explícito `mysql:3306`, mesmo que exista outra `DATABASE_URL` exportada no terminal ou em um segredo do Codespace.

## 2. Construir e subir o ambiente

Ainda em `backend`:

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml config --quiet
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml up --build -d --wait
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml ps
```

O Compose inicia MySQL e Redis. O entrypoint oficial do MySQL executa o SQL quando `/var/lib/mysql` está vazio. Seu health check exige conexão TCP e as 64 tabelas, 121 FKs e 40 CHECKs do domínio; a API aguarda esse estado, aplica suas migrações técnicas existentes e inicia o Uvicorn.

As senhas geradas são compatíveis com a URL utilizada pelo Compose. Alterá-las manualmente exige também atualizar as contas dentro do MySQL já inicializado; mudar somente o arquivo não altera a senha armazenada no volume.

Se o build da API precisar de uma CA de proxy, siga o [build com proxy](../../README.md#build-com-proxy) para construir `prontuario-backend-dev`. Em seguida, use os mesmos argumentos de Compose para executar `build mysql` e `up -d --no-build --wait`. O modo MySQL local utiliza a rede privada de desenvolvimento, `APP_ENV=development` e conexão sem CA externa; não deve ser utilizado para produção ou rede não confiável.

## 3. Conferir a criação do banco

A query de criação já está no [SQL embarcado](../../docs/database/prontuarioedu_mysql.sql):

```sql
CREATE DATABASE IF NOT EXISTS `prontuarioedu`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `prontuarioedu`;
SET NAMES utf8mb4;
SET time_zone = '+00:00';
```

Depois dela, o arquivo cria as 64 tabelas de domínio, FKs, CHECKs e índices. Para consultar os objetos sem colocar senha na linha de comando:

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml exec mysql sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" mysql --protocol=TCP -h 127.0.0.1 -u "$MYSQL_USER" --database=prontuarioedu -e "SHOW TABLES"'
```

Com a API iniciada, são **67 tabelas**: 64 do domínio, `record_permissions`, `audit_events` e `alembic_version`. As tabelas técnicas são geridas pelo Alembic, separadamente do SQL inicial. A tabela `alembic_version` contém o controle de migração; as tabelas de aplicação iniciam sem dados.

## 4. Conectar o cliente MySQL e acessar a API

| Cliente | Host | Porta | Banco / credenciais |
| --- | --- | --- | --- |
| API no Compose | `mysql` | `3306` | URL configurada automaticamente pelo modo MySQL |
| Extensão MySQL ou cliente no Codespace/host Docker | `127.0.0.1` | `3306`, ou `MYSQL_PORT` | Banco `prontuarioedu`, usuário `MYSQL_USER` e senha `MYSQL_PASSWORD` do arquivo privado |

A porta MySQL é publicada somente no loopback do ambiente Docker. No Codespace, o cliente da extensão roda no ambiente remoto; não encaminhe a porta 3306 para acesso público. O nome `mysql` é resolvido na rede do Compose, não no navegador ou no seu computador.

Para conferir a API pelo terminal:

```bash
curl --fail --show-error http://127.0.0.1:8000/health
```

Resultado esperado: `{"status":"ok","database":"ok"}`. No Codespace, configure o hostname em `ALLOWED_HOSTS` no `.env`, encaminhe a porta 8000 com visibilidade privada e abra `/docs`, conforme o [roteiro do backend](../../README.md#rodar-o-contêiner-de-desenvolvimento-e-acessar-a-api). Nos comandos desse roteiro, acrescente sempre `--env-file .env.mysql -f compose.yaml -f compose.mysql.yaml` ao usar este modo.

Se a porta 3306 estiver ocupada, ajuste `MYSQL_PORT` em `.env.mysql`. Isso altera apenas a porta publicada para o cliente; a API continua usando `mysql:3306`. Para mudar a porta HTTP publicada, acrescente `BACKEND_PORT` ao mesmo arquivo.

## 5. Logs, parada e persistência

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml logs -f mysql backend
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml down
```

O volume nomeado `mysql_dev_data` preserva o banco após `down`. A inicialização SQL ocorre somente no primeiro uso de um volume vazio. Reiniciar os serviços ou reconstruir a imagem não reaplica o arquivo e não apaga os dados. Para apenas reiniciar:

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml up -d --wait
```

Alterações futuras do schema de um volume existente precisam de migrações próprias. O health check detecta contagens incompatíveis, mas não substitui uma estratégia de versionamento e migração. Se o primeiro import falhar, examine os logs antes de reutilizar o volume: DDL MySQL pode deixar objetos parcialmente criados.

O usuário técnico deste modo tem privilégios no database de desenvolvimento para permitir o Alembic e seus triggers. `log_bin_trust_function_creators=ON` é aplicado somente ao serviço MySQL deste modo. Uma implantação real exige contas de runtime e migração separadas, TLS e autorização operacional, conforme o [guia MySQL](../../MYSQL.md).

## Verificações realizadas

O teste integrado constrói as imagens atuais e usa um projeto Compose temporário, com portas aleatórias e volume exclusivo. Confere as 64 tabelas de domínio, 121 FKs, 40 CHECKs e 30 índices explícitos; aplica as migrações técnicas; consulta `/health` e `/docs`; testa rejeição de FK inválida, CHECK e duplicidade em índice UNIQUE condicional. Os dados de teste são revertidos e as tabelas de aplicação permanecem vazias.

Também reinicia o MySQL com o volume existente e verifica preservação do schema, da versão Alembic e recuperação da conexão da API. Os contêineres e volumes do teste são removidos ao final; o banco real não participa da validação. Isso valida infraestrutura e constraints, sem implementar Models, rotas clínicas ou as regras de negócio propostas.
