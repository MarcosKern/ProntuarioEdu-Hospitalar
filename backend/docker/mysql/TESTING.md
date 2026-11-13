# Compose de testes com conexão fixa

O arquivo [`compose.test.yaml`](../../compose.test.yaml) inicia MySQL, Redis e API com credenciais públicas e fixas para testes. Ele é independente de `.env.mysql` e do Compose de desenvolvimento. O script usa um arquivo de ambiente vazio para impedir a leitura implícita do `.env` pelo Compose; o contêiner da API recebe somente as variáveis declaradas nesse Compose.

## Subir e exibir a conexão no terminal

Com Python e Docker/Compose disponíveis, execute de `backend`:

```bash
python3 scripts/test_env.py
```

O comando constrói as imagens, inicia os serviços e aguarda todos ficarem `healthy`. **Somente depois disso**, imprime host, porta, database, usuário, senhas, URLs SQL, URL da API e endereço do Swagger. Se o build ou o health check falhar, os dados de conexão não são exibidos como se o ambiente estivesse pronto.

Os valores padrão são:

| Variável / destino | Valor fixo |
| --- | --- |
| `MYSQL_HOST` para cliente no host/Codespace | `127.0.0.1` |
| Porta SQL publicada | `3307` |
| `MYSQL_DATABASE` usado pela API | `prontuarioedu` |
| `MYSQL_USER` | `prontuario_test` |
| `MYSQL_PASSWORD` | `test-only-password` |
| `MYSQL_ROOT_PASSWORD` | `test-only-root-password` |
| Banco separado para pytest | `prontuario_test` |
| `MYSQL_TEST_ALLOW_RESET` | `prontuario_test` |
| API no terminal do host/Codespace | `http://127.0.0.1:8001` |
| Swagger no terminal do host/Codespace | `http://127.0.0.1:8001/docs` |

Essas credenciais são intencionalmente versionadas e exibidas para conexão ao **ambiente de testes**, com portas publicadas apenas no loopback. Elas autenticam a conexão SQL, não um usuário do ProntuarioEdu. O usuário da API não recebe a senha root. A URL da API dentro do Docker usa o hostname `mysql` e a porta `3306`; as URLs impressas usam `127.0.0.1:3307` para conexão por extensão MySQL ou outro cliente no ambiente Docker.

O banco `prontuarioedu` é inicializado com as 64 tabelas de domínio e recebe as migrações técnicas da API. O script [`20-test-database.sql`](20-test-database.sql), embarcado somente no estágio `test` da imagem MySQL, cria também `prontuario_test` e concede ao usuário de teste os privilégios necessários nesse banco. Os arquivos SQL têm permissão de leitura definida no build. A suíte pode limpar suas tabelas técnicas nesse segundo database sem apagar as tabelas usadas pela API.

## Consultar novamente ou parar

```bash
python3 scripts/test_env.py info
python3 scripts/test_env.py down
```

O primeiro comando só exibe as conexões se os serviços estiverem saudáveis. O segundo encerra os contêineres e preserva o volume `mysql_test_data`. A importação inicial ocorre apenas no primeiro uso de um volume vazio. Para iniciar com imagens já construídas:

```bash
python3 scripts/test_env.py --no-build
```

Se a instalação da API exigir uma CA de proxy, use o [build com proxy](../../README.md#build-com-proxy), trocando o nome da imagem de saída para `prontuario-backend-test`. Construa a imagem MySQL com `docker compose -f compose.test.yaml build mysql` e execute o script com `--no-build`.

## Habilitar o login da aplicação neste ambiente

Por padrão, o Compose de testes não recebe a chave JWT de `.env` nem cria usuários. Saúde e documentação funcionam, mas o login retorna `503` enquanto `AUTH_JWT_SECRET` estiver ausente. A chave pode ser fornecida explicitamente pelo processo que inicia o script; usuário e senhas SQL continuam fixos.

1. Prepare o venv com `requirements-dev.txt` conforme o [README do backend](../../README.md#modo-a--python-local).
2. Crie privadamente `backend/.env.test`, já ignorado pelo Git, e inclua `AUTH_JWT_SECRET` com uma chave aleatória conforme o [guia de autenticação](../../AUTHENTICATION.md#configuração). Use uma chave exclusiva de testes; não copie credenciais de produção. Em Linux/Codespaces, execute `chmod 600 .env.test`.
3. De `backend`, forneça o arquivo ao processo de inicialização:

```bash
.venv/bin/python -m dotenv -f .env.test run -- .venv/bin/python scripts/test_env.py
```

O script continua sem carregar `.env`; o Compose recebe a chave do processo explicitamente. A chave JWT não é impressa nas conexões. Mudanças nela exigem executar novamente o comando para recriar a API. Use `--no-build` somente se as imagens já contiverem o código e os requisitos atuais.

4. Com os serviços saudáveis, crie o administrador **no database `prontuarioedu` da API de testes**, pelo comando explícito:

```bash
docker compose --project-name prontuario-test --env-file .env.test -f compose.test.yaml \
  exec backend python scripts/create_admin.py
```

Digite a senha no prompt, sem gravá-la no arquivo. Esse comando usa a conexão fixa do contêiner; não usa `MYSQL_TEST_URL` nem cria conta no database descartável `prontuario_test`. Se iniciou o script com outro `--project-name`, use o mesmo nome neste comando. O cadastro não é um seed nem acontece na subida dos serviços.

5. Abra `http://127.0.0.1:8001/docs`, use **Authorize** com o administrador criado e os escopos `identity:read` e `admin:access`, e execute `/api/v1/admin/me`. No Codespace, use o endereço privado indicado pelo script. Veja [como entrar e conferir](../../ADMINISTRADOR.md#entrar-e-conferir).

## Executar a suíte no banco separado

Depois de subir o Compose, de `backend`, use a URL `MYSQL_TEST_URL` exibida no terminal. Com as portas padrão:

```bash
APP_ENV=test MYSQL_SSL_CA='' \
MYSQL_TEST_URL='mysql+pymysql://prontuario_test:test-only-password@127.0.0.1:3307/prontuario_test?charset=utf8mb4' \
MYSQL_TEST_ALLOW_RESET=prontuario_test \
.venv/bin/python -m pytest -q
```

O venv e as dependências de desenvolvimento são necessários para pytest. A suíte apaga tabelas técnicas em `prontuario_test`; não substitua esse destino pelo banco `prontuarioedu` da API. Consulte o [guia de testes](../../tests/README.md) para os limites e a proteção contra uso do banco da aplicação.

## Codespace e portas alternativas

No Codespace, o script autoriza o hostname exato da porta HTTP e imprime também `SWAGGER_CODESPACE_URL`. Na aba **Ports**, encaminhe a porta 8001 com visibilidade **Private** e abra esse endereço. O cliente MySQL da extensão conecta a `127.0.0.1:3307` dentro do Codespace; não é preciso publicar a porta SQL para o navegador.

Se uma porta estiver ocupada, use `MYSQL_TEST_PORT` e `BACKEND_TEST_PORT` no processo do script. As credenciais permanecem fixas e as portas realmente publicadas são mostradas no terminal. No Codespace, a porta HTTP precisa ser fixa entre 1 e 65535 para gerar o hostname correto.

Para um projeto de testes separado, o script aceita `--project-name`. Use o mesmo nome nas operações `up`, `info` e `down`; cada projeto tem seu próprio volume. Portas também precisam ser distintas quando houver execução simultânea.

## Validação histórica do Compose completo

O Compose e o comando foram executados em projeto temporário: a exibição foi bloqueada antes da subida e após a parada, e as conexões publicadas no host funcionaram com as credenciais fixas. Variáveis conflitantes no processo e em `.env` não substituíram usuário, senhas ou destino da API. A senha root não estava no ambiente do serviço da API.

Nessa verificação anterior, **46 testes passaram** contra `prontuario_test`, enquanto a API permaneceu saudável em `prontuarioedu`. O projeto e o volume temporários foram removidos ao final. Nenhum banco real ou configuração privada de desenvolvimento participou do teste. Esse número não representa a suíte atual; as verificações mais recentes, incluindo os limites do build nesta nuvem, estão no [acompanhamento F01](../../docs/F01.md).
