# ProntuarioEdu-Hospitalar

API de prontuário educacional compartilhada por Desktop Python, Web responsiva e futuras integrações. O backend usa **Python 3.12, FastAPI MVC, MySQL 8.4, SQLAlchemy/PyMySQL, Alembic e JWT local**. Desktop e Web ainda não têm aplicações executáveis; a tecnologia da Web e o toolkit Desktop estão em aberto.

## Começar

**[Subir Docker e abrir o Swagger → backend/README.md](backend/README.md)**

Esse é o roteiro de execução do projeto: preparar as ferramentas e a configuração privada, iniciar API + MySQL + Redis, criar o administrador, abrir o Swagger e fazer a primeira chamada autenticada. Use esse guia tanto no computador quanto depois de preparar um Codespace.

| Preciso de… | Documento responsável |
| --- | --- |
| Criar ou reconstruir o editor no GitHub Codespaces | [Configuração do Codespace](.devcontainer/README.md) |
| Entender MVC, as pastas e a divisão de trabalho | [Arquitetura](docs/architecture.md) |
| Desenvolver a API pelo Python, sem contêiner da API | [Desenvolvimento do backend](backend/docs/DESENVOLVIMENTO.md) |
| Executar testes e usar um banco descartável | [Testes do backend](backend/tests/README.md) |
| Consultar autenticação, banco, contratos e segurança | [Índice técnico](docs/README.md) |
| Rodar em servidor e planejar produção | [Hospedagem](infra/README.md) |

## Organização do repositório

```text
backend/        API, scripts, migrations, Compose, testes e referências técnicas
  README.md     Roteiro único: Docker → administrador → Swagger
  src/          Código Python MVC
  tests/        Suíte e seu guia de execução
  docs/         Autenticação, MySQL, contratos, segurança e modelo de dados
  docker/mysql/ Imagem e inicialização do MySQL de desenvolvimento/testes
.devcontainer/  Ferramentas e extensões do Codespace
desktop/        Estrutura prevista do cliente Python
web/            Estrutura prevista do cliente responsivo
contracts/      Exportação OpenAPI e compatibilidade entre clientes
docs/           Arquitetura, decisões, governança e histórico
infra/          Orientação de hospedagem; não contém outro Compose
```

O ambiente não cria pacientes ou usuários automaticamente. O administrador é criado explicitamente por comando e sua senha fica como hash no MySQL. O SQL de domínio é inicializado somente nos modos de desenvolvimento/testes escolhidos, em volume vazio.

As decisões aprovadas estão nas [ADRs](docs/adr/README.md). As regras para alterações e merge estão em [governança](docs/repository-governance.md) e [AGENTS.md](AGENTS.md).
