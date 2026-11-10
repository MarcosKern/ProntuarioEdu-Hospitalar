# Ambiente padronizado no GitHub Codespaces

O arquivo [devcontainer.json](devcontainer.json) define o ambiente do editor, sem alterar a imagem de produção da API. A imagem de desenvolvimento usa Python 3.12 e usuário `vscode`; a imagem do Back-end continua separada em `backend/Dockerfile`.

## Instalação automática

| Item | Configuração |
| --- | --- |
| Python 3.12 e venv | Imagem oficial Dev Containers para Python |
| Dependências da equipe | `backend/requirements-dev.txt`, que inclui o runtime fixado |
| Docker Engine, Compose v2 e Buildx | Feature oficial Docker in Docker |
| Python e análise de tipos | `ms-python.python` e `ms-python.vscode-pylance` |
| Lint e formatação | `charliermarsh.ruff` |
| Postman | `Postman.postman-for-vscode` |
| Cliente de banco MySQL | `cweijan.vscode-mysql-client2` |
| Interface para imagens/contêineres | `ms-azuretools.vscode-containers` |

A configuração declara as extensões; o GitHub/VS Code baixa-as no Codespace. Recursos de terceiros podem exigir login, licença ou abertura no VS Code Desktop conforme sua disponibilidade. Nenhuma conta, senha, conexão MySQL ou coleção Postman com credenciais é embutida no repositório.

## Criar ou atualizar um Codespace

1. Disponibilizar estes arquivos na branch que deseja usar. No GitHub: **Code → Codespaces → Create codespace** nessa branch.
2. Aguardar o build da imagem, instalação da feature Docker e conclusão do `postCreateCommand`.
3. O script [setup.py](setup.py) prepara `backend/.venv`, instala o lock dev e cria `backend/.env` a partir do exemplo **somente se não existir**. Não importa SQL, não executa Alembic e não inicia a API.
4. Em Codespace existente, usar **Dev Containers: Rebuild Container** após mudar `devcontainer.json`. Para apenas reaplicar dependências, executar da raiz `python3 .devcontainer/setup.py`.
5. Conferir no terminal `python --version`, `python -m pip check`, `docker info` e `docker compose version`.

A feature Docker necessita permissões do ambiente de contêineres e pode ser bloqueada por política da organização. Não iniciar outro daemon manualmente para contornar uma falha. O primeiro build pode demorar; os locks Python são fixados, enquanto tags de imagem/feature recebem manutenção do provedor.

## Configurar MySQL externo e segredos

Use **Settings → Secrets and variables → Codespaces** do GitHub, ou seus segredos pessoais de Codespaces, habilitando acesso ao repositório. Configure `DATABASE_URL` e, quando necessário, os valores `OIDC_*`. Reinicie/recrie o Codespace para receber alterações de segredos. Não colocar valores em `devcontainer.json`, tasks, conexões versionadas ou mensagens de commit.

A variável exportada pelo Codespaces tem precedência sobre `.env`. Alternativamente, preencher `backend/.env` privadamente. O formato aceito é `mysql+pymysql://...`, com credenciais percent-encoded. Certificados não são segredos em variável de texto: disponibilizar o arquivo CA confiável no Codespace e apontar `MYSQL_SSL_CA` para seu caminho.

O banco é **MySQL 8.4 externo**: este Dev Container não instala MySQL Server e não conecta o navegador diretamente ao banco. O hostname deve ser acessível a partir do Codespace e aceito pelo certificado; `localhost` não aponta para seu computador ou servidor externo. O operador pode precisar autorizar a rede do Codespaces ou disponibilizar conectividade privada. A senha é fornecida de forma segura, nunca por URL no histórico do terminal.

O cliente MySQL do VS Code deve usar o mesmo servidor/banco e verificar TLS, com usuário de privilégios mínimos. Não versionar configurações de conexão contendo credenciais. A extensão não aplica as regras de autorização da API: acesso SQL deve ser limitado a quem tem essa competência.

## Iniciar a API e usar o Postman

Pela paleta **Tasks: Run Task**, escolha **Codespaces: iniciar API**. Alternativamente, da raiz:

```bash
backend/.venv/bin/python .devcontainer/start.py
```

O comando chama o `backend/scripts/dev.py` existente. **Ao iniciar a API ele aplica migrações técnicas Alembic no MySQL configurado**: use banco de desenvolvimento autorizado, nunca produção.

O wrapper acrescenta ao processo apenas o hostname exato de encaminhamento do Codespace, sem wildcard e sem sobrescrever `.env`. A porta 8000 é encaminhada. Na aba **Ports**, mantenha a visibilidade **Private** e abra o endereço fornecido pelo Codespaces; a configuração não publica uma porta pública automaticamente.

- `/health`: verificar acesso SQL real.
- `/docs`: Swagger em desenvolvimento.
- `/openapi.json`: importar a especificação no Postman.
- `/api/v1/me`: sem token, retorna 401; exige provedor OIDC configurado para login real.

Para requisições executadas dentro do Codespace, usar o loopback da API. Para requisições externas, usar a URL encaminhada privada e sua autenticação de acesso do GitHub; a autenticação do túnel é diferente do token OAuth2 da API. Não tornar a porta pública para contornar falhas. Se o Postman não tiver todos os recursos na edição web, abrir o Codespace no VS Code Desktop ou usar Swagger/cliente HTTP no terminal.

Para outra porta: `backend/.venv/bin/python .devcontainer/start.py --port 8001` e encaminhá-la manualmente. Ctrl+C encerra a API. A tarefa funciona com ou sem provedor OIDC, mas endpoints protegidos continuam bloqueados sem configuração válida.

## Testes e Docker

As tarefas **Backend: testes** e **Backend: lint** usam o venv e o diretório corretos. Testes de banco precisam de `MYSQL_TEST_URL` e `MYSQL_TEST_ALLOW_RESET` para banco descartável separado; nunca usar o banco da aplicação. A descoberta automática do pytest no editor não autoriza executar testes destrutivos no banco real. Siga [o guia de testes](../backend/tests/README.md).

É possível executar o Compose da API dentro do Codespace:

```bash
cd backend
docker compose config --quiet
docker compose up --build -d --wait
```

Não executar junto à API local na mesma porta. Compose inicia API e Redis, não MySQL. Para esse caminho com URL encaminhada, incluir o hostname exato do Codespace em `ALLOWED_HOSTS` (JSON) no `.env`/segredo antes de recriar o serviço: o wrapper de inicialização local não modifica o ambiente de um contêiner Compose independente. Certificados MySQL precisam da montagem do [override TLS](../backend/compose.tls.yaml) e caminhos do arquivo visíveis ao daemon Docker interno.

## Limite da validação

A configuração pode ser lida pela CLI oficial Dev Containers sem iniciar uma máquina. A validação completa do build da feature, instalação das extensões e encaminhamento privado exige um Codespace real. Nenhum Codespace pago é criado automaticamente por estes scripts.
