# Instruções do projeto

## Componentes

- Back-end em Python: centraliza regras de negócio, autenticação e acesso aos dados.
- Desktop em Python: consome contratos públicos do back-end.
- Web responsiva e compatível com dispositivos móveis: tecnologia ainda não escolhida.
- Novos aplicativos devem poder integrar-se pelos mesmos contratos públicos.

## Arquitetura

O responsável escolheu MVC para simplificar o Back-end: Models, Views e Controllers, com rotas e configuração de apoio. A decisão está na ADR 0001. Não recrie camadas hexagonais no servidor. O ambiente de desenvolvimento usa FastAPI, SQLAlchemy/MySQL e validação OAuth2/OIDC por JWT, conforme ADR 0004. Provedor real e tecnologias dos clientes permanecem pendentes. Antes de novas decisões arquiteturais ou dependências de aplicação, registre alternativas, justificativa e testes em ADR e obtenha aprovação explícita do responsável. Veja `docs/architecture-options.md`.

## Git e revisão

Atualização da identidade de desenvolvimento: o responsável escolheu Keycloak no Docker e autorizou o primeiro usuário `admin` da aplicação (ADR 0009). `backend/scripts/auth_dev.py up --with-backend` pode cadastrar esse usuário, perfil, permissão e auditoria somente no modo MySQL de desenvolvimento explícito. Não criar dados clínicos nem reativar concessões revogadas. Senhas/chaves ficam em `backend/.local/auth`, fora do Git/build, e não devem ser impressas. Administradores de infraestrutura são separados dos usuários da aplicação. A identidade de produção continua pendente.

- Criar branches é permitido sem autorização adicional.
- Antes de excluir branches, reescrever seu histórico ou alterar branches existentes, obtenha autorização explícita do responsável, salvo autorização já dada para a operação específica. Isso inclui commits, pushes e merges em branches existentes; criar uma branch de trabalho não autoriza alterar outras branches.
- Não execute merge sem pelo menos quatro aprovações humanas válidas, revisão automática do Codex concluída, bloqueios resolvidos e validação arquitetural aplicável aprovada.
- Revisões automáticas não substituem as quatro aprovações humanas.
- Preserve estas regras em toda proposta de automação. Instruções neste arquivo não substituem a proteção de branches no GitHub.

## Ambiente

Use o checkout existente em `/workspace/ProntuarioEdu-Hospitalar`. Não crie worktrees, salvo solicitação explícita. De `backend`, executar `python scripts/dev.py --setup` para preparar/iniciar o venv, ou `docker compose up --build -d --wait`. Testar com `.venv/bin/python -m pytest -q`; integração MySQL exige banco separado e `MYSQL_TEST_ALLOW_RESET` igual ao nome do banco de teste. Consulte o README para configuração e limites.

## Banco e Codespaces

MySQL 8.4 é o único mecanismo suportado. Requirements não devem incluir drivers de outro mecanismo. O responsável autorizou os documentos em `backend/docs/database` e a inicialização do SQL no modo opcional `backend/compose.mysql.yaml` de desenvolvimento, conforme ADR 0008. Fora desse modo explícito, não importar o SQL automaticamente nem aplicá-lo ao servidor externo. O Alembic técnico permanece separado. Models, rotas clínicas e integrações de domínio continuam pendentes. Não criar dados de demonstração. O Dev Container prepara ferramentas e extensões sem conectar ou migrar banco; a inicialização da API e a escolha do modo de banco são ações separadas.

O responsável também autorizou `backend/compose.test.yaml` com credenciais fixas e exibição das conexões por `scripts/test_env.py` após os serviços ficarem saudáveis. A inicialização é permitida nesse modo explícito de testes; não aplica SQL em servidor externo. O database `prontuario_test` é reservado à suíte, separado de `prontuarioedu`, e o volume de testes não é compartilhado com o desenvolvimento. Apenas as credenciais públicas desse modo devem ser exibidas; não imprimir segredos de `.env` ou `.env.mysql`.
