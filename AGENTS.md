# Instruções do projeto

## Componentes

- Back-end em Python: centraliza regras de negócio, autenticação e acesso aos dados.
- Desktop em Python: consome contratos públicos do back-end.
- Web responsiva e compatível com dispositivos móveis: tecnologia ainda não escolhida.
- Novos aplicativos devem poder integrar-se pelos mesmos contratos públicos.

## Arquitetura

O responsável escolheu MVC para simplificar o Back-end: Models, Views e Controllers, com rotas e configuração de apoio. A decisão está na ADR 0001. Não recrie camadas hexagonais no servidor. O ambiente de desenvolvimento usa FastAPI, SQLAlchemy/MySQL e validação OAuth2/OIDC por JWT, conforme ADR 0004. Provedor real e tecnologias dos clientes permanecem pendentes. Antes de novas decisões arquiteturais ou dependências de aplicação, registre alternativas, justificativa e testes em ADR e obtenha aprovação explícita do responsável. Veja `docs/architecture-options.md`.

## Git e revisão

- Criar branches é permitido sem autorização adicional.
- Antes de excluir branches, reescrever seu histórico ou alterar branches existentes, obtenha autorização explícita do responsável, salvo autorização já dada para a operação específica. Isso inclui commits, pushes e merges em branches existentes; criar uma branch de trabalho não autoriza alterar outras branches.
- Não execute merge sem pelo menos quatro aprovações humanas válidas, revisão automática do Codex concluída, bloqueios resolvidos e validação arquitetural aplicável aprovada.
- Revisões automáticas não substituem as quatro aprovações humanas.
- Preserve estas regras em toda proposta de automação. Instruções neste arquivo não substituem a proteção de branches no GitHub.

## Ambiente

Use o checkout existente em `/workspace/ProntuarioEdu-Hospitalar`. Não crie worktrees, salvo solicitação explícita. De `backend`, executar `python scripts/dev.py --setup` para preparar/iniciar o venv, ou `docker compose up --build -d --wait`. Testar com `.venv/bin/python -m pytest -q`; integração MySQL exige banco separado e `MYSQL_TEST_ALLOW_RESET` igual ao nome do banco de teste. Consulte o README para configuração e limites.

## Banco e Codespaces

MySQL 8.4 é o único mecanismo suportado. Requirements não devem incluir drivers de outro mecanismo. O responsável autorizou incorporar os documentos recebidos, revisados para MySQL, em `backend/docs/database`. O SQL dessa pasta é referência documental, separado do Alembic técnico atual. A implementação das tabelas de domínio, Models, rotas e integrações permanece adiada até solicitação explícita; não importar o SQL automaticamente. Não criar dados de demonstração. O Dev Container prepara ferramentas e extensões sem conectar ou migrar banco; a inicialização da API é uma ação separada.
