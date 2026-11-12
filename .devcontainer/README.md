# Ambiente padronizado no GitHub Codespaces

O arquivo [devcontainer.json](devcontainer.json) define o ambiente do editor, sem alterar a imagem de produção da API. O [Dockerfile de desenvolvimento](Dockerfile) usa a imagem oficial Python 3.12 e remove a fonte APT desnecessária do Yarn antes da instalação das features. O editor usa o usuário `vscode`; a imagem do Back-end continua separada em `backend/Dockerfile`.

## Passo a passo para executar a configuração no GitHub

O `devcontainer.json` é um arquivo de configuração lido pelo GitHub Codespaces. Você não precisa executá-lo com Python, instalar as extensões uma por uma ou montar um contêiner manualmente. O GitHub lê esse arquivo quando cria ou reconstrói o Codespace e executa as etapas descritas abaixo.

Este procedimento prepara apenas o ambiente de desenvolvimento. Não é necessário configurar uma conexão MySQL para concluí-lo. O banco e a arquitetura enviados pelo responsável continuam adiados; nenhum anexo é importado por essa configuração.

### 1. Confirmar que a configuração está na branch do GitHub

Abra o repositório no GitHub e use o seletor de branches, acima da lista de arquivos, para escolher a branch de trabalho. Confirme que ela contém `.devcontainer/devcontainer.json`, `.devcontainer/Dockerfile` e `.devcontainer/setup.py`.

Se os arquivos estiverem apenas no computador ou em outro ambiente, primeiro é necessário enviar a branch ao GitHub. Por exemplo, para a branch criada para esta configuração, execute no terminal do repositório:

```bash
git push -u origin chore/codespaces-mysql-dev-environment
```

Esse comando é uma etapa manual de publicação da branch; não faz parte da execução automática do Codespace. Se a configuração estiver em outra branch, use o nome correspondente.

### 2. Criar o Codespace na branch escolhida

Com a branch correta selecionada, clique no botão **Code**, abra a aba **Codespaces** e escolha **Create codespace on ...**. Confira se o nome exibido é o da branch que contém a configuração.

Se a tela oferecer a escolha da configuração de Dev Container, selecione a que corresponde a `.devcontainer/devcontainer.json`, identificada como **ProntuarioEdu — desenvolvimento Python 3.12**. Aguarde o GitHub abrir o editor no navegador.

### 3. Aguardar o GitHub executar o arquivo de configuração

Durante a criação, o GitHub lê o `devcontainer.json`, constrói a imagem Python 3.12 pelo Dockerfile, instala a feature Docker e solicita as extensões declaradas. Em seguida, executa automaticamente o `postCreateCommand`:

```bash
python3 .devcontainer/setup.py
```

O script cria `backend/.venv`, instala `backend/requirements-dev.txt` e verifica a compatibilidade das dependências com `pip check`. Também cria `backend/.env` a partir de `.env.example` somente se o arquivo ainda não existir, preservando a configuração existente.

Não execute esse comando em paralelo enquanto a preparação automática estiver em andamento. Aguarde o término do processo; quando houver a opção **View creation log** / **Exibir log de criação**, acompanhe por ela. Ao concluir o script, o log deve conter:

```text
Dependências prontas. Configure MySQL e AUTH_JWT_SECRET e use a tarefa Codespaces: iniciar API.
Nenhum SQL foi importado e nenhuma migração foi executada.
```

A mensagem sobre iniciar a API indica uma etapa posterior. A API não é iniciada por esse script.

### 4. Conferir se o ambiente ficou pronto

No editor do Codespace, abra **Terminal → New Terminal**. Os comandos abaixo devem ser executados na raiz do repositório, onde aparecem as pastas `backend` e `.devcontainer`:

```bash
pwd
backend/.venv/bin/python --version
backend/.venv/bin/python -m pip check
docker info
docker compose version
```

O Python deve ser `3.12.x`; o `pip check` deve informar `No broken requirements found.`. O `docker info` deve mostrar informações do servidor Docker, e o último comando deve apresentar a versão do Compose. Se uma etapa falhar, consulte o log antes de considerar a instalação concluída.

Abra também **Extensions** na barra lateral e confira as extensões listadas na tabela da seção seguinte. Se o Python do editor não estiver apontando para o ambiente do projeto, abra a paleta com `Ctrl+Shift+P` (ou `Cmd+Shift+P` no macOS), execute **Python: Select Interpreter** e escolha `backend/.venv/bin/python`.

Para conferir as ferramentas sem acessar o banco, execute da raiz:

```bash
backend/.venv/bin/python -m ruff check backend/src backend/tests backend/scripts
```

Com essas verificações concluídas, o ambiente está preparado para trabalhar no código. Não é preciso executar a API nem configurar banco de dados nesta etapa.

### 5. Aplicar a configuração em um Codespace já existente

Abra o Codespace e confirme que o checkout contém a versão desejada de `.devcontainer/devcontainer.json` e dos scripts. Reconstruir o contêiner usa os arquivos presentes nesse checkout; não baixa automaticamente alterações de outra branch. Se houver trabalho pendente, preserve-o antes de atualizar ou trocar a branch pelo controle de versão.

Abra a paleta com `Ctrl+Shift+P` (ou `Cmd+Shift+P`) e execute **Codespaces: Rebuild Container**. Dependendo do editor utilizado, o comando pode aparecer como **Dev Containers: Rebuild Container**. Aguarde a reconstrução, a execução do script de preparação e a reabertura do editor. Depois, repita as verificações do passo 4.

Use a reconstrução quando mudar imagem, features ou configuração do contêiner. Apenas fechar e reabrir o editor não garante que essas mudanças sejam aplicadas.

### 6. Reinstalar somente as dependências, quando necessário

Se a configuração do contêiner não mudou e você precisa apenas reaplicar as dependências Python, execute da raiz:

```bash
python3 .devcontainer/setup.py
```

Isso reutiliza o venv existente, preserva `.env` e executa novamente a instalação e o `pip check`. Esse comando sozinho não instala as extensões do VS Code nem o Docker: essas etapas dependem do `devcontainer.json` durante a criação ou reconstrução do Codespace.

### Se a preparação falhar

- **A configuração não foi encontrada:** confira a branch e a presença de `.devcontainer/devcontainer.json` no GitHub. Em Codespace existente, confirme também o checkout e reconstrua o contêiner.
- **Erro de instalação de pacotes:** consulte o log da criação ou a saída do `setup.py`. Depois de resolver a causa, execute novamente o script pelo passo 6.
- **Extensão ausente:** confira a aba Extensions e o log. Alguns recursos podem exigir login, disponibilidade no editor ou permissão da organização.
- **Docker indisponível:** confira se a feature foi instalada e se a política da organização permite seu uso. Consulte os logs da reconstrução antes de tentar novamente.

### Recuperar o Codespace após erro de chave GPG do Yarn

O erro `NO_PUBKEY 62D54FD4003F6525`, seguido de `The repository 'https://dl.yarnpkg.com/debian stable InRelease' is not signed`, pode interromper o `apt-get update` da feature Docker. A falha acontece na construção da imagem, antes de executar `setup.py`, e o GitHub abre um contêiner de recuperação.

O Dockerfile deste projeto remove apenas as fontes `/etc/apt/sources.list.d/yarn.list` e `yarn.sources` herdadas da imagem. O ambiente Python/Docker atual não depende desse repositório. A correção ocorre antes da instalação das features e mantém a verificação de assinaturas dos demais repositórios. Não é necessário importar uma chave manualmente ou desabilitar as verificações do APT.

Para recuperar um Codespace que apresenta essa mensagem:

1. Abra o terminal do contêiner de recuperação e entre na raiz do repositório. Preserve seu trabalho pendente antes de atualizar o checkout.
2. Depois que a correção estiver publicada na branch utilizada pelo Codespace, baixe-a com `git pull --ff-only`, desde que essa branch já acompanhe a correspondente no GitHub. Confira que o `devcontainer.json` possui `build.dockerfile` apontando para `Dockerfile` e que `.devcontainer/Dockerfile` existe. Se a correção estiver em outra branch, disponibilize-a na branch usada antes de reconstruir.
3. Abra a paleta e execute **Codespaces: Rebuild Container** ou **Dev Containers: Rebuild Container**. Apenas executar `setup.py` no contêiner de recuperação não corrige a imagem ou instala a feature Docker.
4. Acompanhe o log até terminar a instalação das features e das dependências Python. Depois, repita as verificações do passo 4 deste guia, incluindo `docker info` e `docker compose version`.

Esse procedimento reconstrói o ambiente de ferramentas. Não inicia a API nem aplica migrações no banco.

## Instalação automática

| Item | Configuração |
| --- | --- |
| Python 3.12 e venv | Imagem oficial Dev Containers para Python, preparada por `.devcontainer/Dockerfile` |
| Dependências da equipe | `backend/requirements-dev.txt`, que inclui o runtime fixado |
| Docker Engine, Compose v2 e Buildx | Feature oficial Docker in Docker |
| Python e análise de tipos | `ms-python.python` e `ms-python.vscode-pylance` |
| Lint e formatação | `charliermarsh.ruff` |
| Postman | `Postman.postman-for-vscode` |
| Cliente de banco MySQL | `cweijan.vscode-mysql-client2` |
| Interface para imagens/contêineres | `ms-azuretools.vscode-containers` |

A configuração declara as extensões; o GitHub/VS Code baixa-as no Codespace. Recursos de terceiros podem exigir login, licença ou abertura no VS Code Desktop conforme sua disponibilidade. Nenhuma conta, senha, conexão MySQL ou coleção Postman com credenciais é embutida no repositório.

A feature Docker necessita permissões do ambiente de contêineres e pode ser bloqueada por política da organização. Não iniciar outro daemon manualmente para contornar uma falha. O primeiro build pode demorar; os locks Python são fixados, enquanto tags de imagem/feature recebem manutenção do provedor.

## Etapa futura: configurar MySQL externo e segredos

Use **Settings → Secrets and variables → Codespaces** do GitHub, ou seus segredos pessoais de Codespaces, habilitando acesso ao repositório. Configure `DATABASE_URL` e `AUTH_JWT_SECRET`. Reinicie/recrie o Codespace para receber alterações de segredos. Não colocar valores em `devcontainer.json`, tasks, conexões versionadas ou mensagens de commit.

A variável exportada pelo Codespaces tem precedência sobre `.env`. Alternativamente, preencher `backend/.env` privadamente. O formato aceito é `mysql+pymysql://...`, com credenciais percent-encoded. Certificados não são segredos em variável de texto: disponibilizar o arquivo CA confiável no Codespace e apontar `MYSQL_SSL_CA` para seu caminho.

O banco é **MySQL 8.4 externo**: este Dev Container não instala MySQL Server e não conecta o navegador diretamente ao banco. O hostname deve ser acessível a partir do Codespace e aceito pelo certificado; `localhost` não aponta para seu computador ou servidor externo. O operador pode precisar autorizar a rede do Codespaces ou disponibilizar conectividade privada. A senha é fornecida de forma segura, nunca por URL no histórico do terminal.

O cliente MySQL do VS Code deve usar o mesmo servidor/banco e verificar TLS, com usuário de privilégios mínimos. Não versionar configurações de conexão contendo credenciais. A extensão não aplica as regras de autorização da API: acesso SQL deve ser limitado a quem tem essa competência.

## Etapa futura: iniciar a API e usar o Postman

Pela paleta **Tasks: Run Task**, escolha **Codespaces: iniciar API**. Alternativamente, da raiz:

```bash
backend/.venv/bin/python .devcontainer/start.py
```

O comando chama o `backend/scripts/dev.py` existente. **Ao iniciar a API ele aplica migrações técnicas Alembic no MySQL configurado**: use banco de desenvolvimento autorizado, nunca produção.

O wrapper acrescenta ao processo apenas o hostname exato de encaminhamento do Codespace, sem wildcard e sem sobrescrever `.env`. A porta 8000 é encaminhada. Na aba **Ports**, mantenha a visibilidade **Private** e abra o endereço fornecido pelo Codespaces; a configuração não publica uma porta pública automaticamente.

- `/health`: verificar acesso SQL real.
- `/docs`: Swagger em desenvolvimento.
- `/openapi.json`: importar a especificação no Postman.
- `/api/v1/me`: sem token, retorna 401; o login local exige chave JWT e usuário cadastrado; veja [autenticação](../backend/AUTHENTICATION.md).

Para requisições executadas dentro do Codespace, usar o loopback da API. Para requisições externas, usar a URL encaminhada privada e sua autenticação de acesso do GitHub; a autenticação do túnel é diferente do token OAuth2 da API. Não tornar a porta pública para contornar falhas. Se o Postman não tiver todos os recursos na edição web, abrir o Codespace no VS Code Desktop ou usar Swagger/cliente HTTP no terminal.

Para outra porta: `backend/.venv/bin/python .devcontainer/start.py --port 8001` e encaminhá-la manualmente. Ctrl+C encerra a API. A tarefa funciona com ou sem chave JWT, mas endpoints protegidos continuam bloqueados sem chave JWT, conta e token válidos.

## Testes e Docker

As tarefas **Backend: testes** e **Backend: lint** usam o venv e o diretório corretos. Testes de banco precisam de `MYSQL_TEST_URL` e `MYSQL_TEST_ALLOW_RESET` para banco descartável separado; nunca usar o banco da aplicação. A descoberta automática do pytest no editor não autoriza executar testes destrutivos no banco real. Siga [o guia de testes](../backend/tests/README.md).

É possível executar o Compose da API dentro do Codespace:

```bash
cd backend
docker compose config --quiet
docker compose up --build -d --wait
```

Não executar junto à API local na mesma porta. O Compose base inicia API e Redis, não MySQL. Para esse caminho com URL encaminhada, incluir o hostname exato do Codespace em `ALLOWED_HOSTS` (JSON) no `.env`/segredo antes de recriar o serviço: o wrapper de inicialização local não modifica o ambiente de um contêiner Compose independente. Certificados MySQL precisam da montagem do [override TLS](../backend/compose.tls.yaml) e caminhos do arquivo visíveis ao daemon Docker interno.

Para iniciar também um MySQL de desenvolvimento com o SQL recebido, siga o [modo opcional MySQL em contêiner](../backend/docker/mysql/README.md). Ele é iniciado por uma ação explícita do desenvolvedor e não pelo `postCreateCommand` do Codespace. Mantenha `ALLOWED_HOSTS` da API no `.env` e a porta SQL restrita ao ambiente remoto.

## Limite da validação

A configuração pode ser lida pela CLI oficial Dev Containers sem iniciar uma máquina. A validação completa do build da feature, instalação das extensões e encaminhamento privado exige um Codespace real. Nenhum Codespace pago é criado automaticamente por estes scripts.
