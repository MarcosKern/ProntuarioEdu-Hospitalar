# Preparar o editor no GitHub Codespaces

Este guia cuida apenas do editor e das ferramentas. **Para iniciar os contêineres e abrir o Swagger, use o [roteiro do backend](../backend/README.md).** Criar/reconstruir o Codespace não inicia a API nem importa SQL ou aplica migrations.

## Criar o Codespace

1. No GitHub, abra o repositório e selecione a branch que contém o código desejado e `.devcontainer/devcontainer.json`.
2. Clique em **Code → Codespaces → Create codespace on…**. Se aparecer uma escolha de configuração, selecione **ProntuarioEdu — desenvolvimento Python 3.12**.
3. Aguarde a criação. Em **View creation log**, acompanhe a instalação; não execute outro setup em paralelo.
4. O GitHub executa `python3 .devcontainer/setup.py`, que cria `backend/.venv`, instala `requirements-dev.txt`, executa `pip check` e copia `.env.example` somente se `.env` ainda não existe.
5. Ao ver a confirmação de dependências prontas e de que nenhuma migration foi executada, abra **Terminal → New Terminal** e confira, da raiz:

```bash
backend/.venv/bin/python --version
backend/.venv/bin/python -m pip check
docker info
docker compose version
```

Espere Python 3.12, dependências consistentes e Docker/Compose funcionando. Em **Python: Select Interpreter**, selecione `backend/.venv/bin/python` se o editor não o tiver escolhido.

Agora siga o [passo 2 do roteiro principal](../backend/README.md#2-preparar-a-configuração-privada). O hostname privado e o encaminhamento da porta são configurados nesse roteiro, junto do serviço que será acessado.

## Atualizar um Codespace existente

Preserve seu trabalho e confira se o checkout contém a configuração desejada. Abra a paleta (`Ctrl+Shift+P` ou `Cmd+Shift+P`) e execute **Codespaces: Rebuild Container** ou **Dev Containers: Rebuild Container**. Aguarde a reconstrução e repita as verificações acima. Reabrir a aba não reconstrói o ambiente nem troca sua branch.

Se mudou apenas dependências Python, execute da raiz:

```bash
python3 .devcontainer/setup.py
```

Esse comando preserva `.env` e reutiliza o venv. Ele não reinstala extensões nem Docker; essas partes dependem da criação/reconstrução do Dev Container.

## O que é instalado

| Ferramenta | Configuração |
| --- | --- |
| Python 3.12 e venv | Dockerfile de desenvolvimento |
| Dependências e Ruff | `backend/requirements-dev.txt` |
| Docker, Compose v2 e Buildx | Feature oficial Docker in Docker |
| Python/Pylance | `ms-python.python`, `ms-python.vscode-pylance` |
| Formatação | `charliermarsh.ruff` |
| Cliente HTTP | `Postman.postman-for-vscode` |
| Cliente MySQL | `cweijan.vscode-mysql-client2` |
| Contêineres | `ms-azuretools.vscode-containers` |

Confira as extensões na aba **Extensions**. Recursos de terceiros podem exigir login ou VS Code Desktop. Nenhuma conexão SQL, senha ou token é incluído na configuração versionada.

## Resolver problemas de criação

- **Configuração não encontrada:** confira a branch e a presença de `.devcontainer/devcontainer.json` no checkout.
- **Dependências não instalaram:** confira o log, resolva o acesso ao índice de pacotes e execute novamente o setup.
- **Docker indisponível:** confira a instalação da feature e as políticas da organização; não inicie um segundo daemon para contornar a falha.
- **Recovery mode / erro GPG do Yarn `NO_PUBKEY 62D54FD4003F6525`:** a correção está no Dockerfile, que remove apenas a fonte Yarn não utilizada antes de instalar as features. Atualize o checkout preservando seu trabalho e reconstrua o contêiner. Executar somente `setup.py` no recovery não corrige a imagem. Não desative a verificação de assinaturas do APT.

Verificar arquivos e comandos localmente não comprova instalação das extensões ou funcionamento do túnel GitHub. Esses passos precisam ser conferidos em um Codespace real.
