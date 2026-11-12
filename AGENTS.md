# Instruções do projeto

## Componentes

- Back-end em Python: centraliza regras de negócio, autenticação e acesso aos dados.
- Desktop em Python: consome contratos públicos do back-end.
- Web responsiva e compatível com dispositivos móveis: tecnologia ainda não escolhida.
- Novos aplicativos devem poder integrar-se pelos mesmos contratos públicos.

## Arquitetura

O responsável escolheu MVC para simplificar o Back-end: Models, Views e Controllers, com rotas e configuração de apoio (ADR 0001). Não recrie camadas hexagonais. Em 12/11/2026, autorizou a remoção do Keycloak e escolheu login na própria API com usuário/senha MySQL e JWT (ADR 0010). Manter FastAPI, SQLAlchemy/PyMySQL síncrono e as dependências existentes; não reintroduzir um provedor de identidade, cofre ou serviços de autenticação adicionais sem solicitação. Antes de outras decisões arquiteturais ou dependências de aplicação, registrar alternativas, justificativa e testes em ADR e obter aprovação explícita. Tecnologias dos clientes continuam pendentes.


## Git e revisão

O administrador local é criado explicitamente por `backend/scripts/create_admin.py`, no banco configurado na execução. Senha digitada por `getpass`, armazenada somente como hash scrypt; não imprimir nem salvar senha em arquivo. `--convert-existing` autoriza converter uma conta externa preservando ID e permissões; nunca tomar outra conta, reativar usuários ou refazer concessões revogadas. JWT exige `AUTH_JWT_SECRET` privado; refresh tokens aleatórios ficam como hashes e as sessões são verificadas no MySQL em cada requisição. Não criar dados clínicos. Credenciais de infraestrutura são separadas dos usuários da aplicação. `.env`, `.env.mysql` e `.local/` continuam ignorados. Não apagar volumes de instalações antigas nem redefinir suas senhas automaticamente.


- Criar branches é permitido sem autorização adicional.
- Antes de excluir branches, reescrever seu histórico ou alterar branches existentes, obtenha autorização explícita do responsável, salvo autorização já dada para a operação específica. Isso inclui commits, pushes e merges em branches existentes; criar uma branch de trabalho não autoriza alterar outras branches.
- Não execute merge sem pelo menos quatro aprovações humanas válidas, revisão automática do Codex concluída, bloqueios resolvidos e validação arquitetural aplicável aprovada.
- Revisões automáticas não substituem as quatro aprovações humanas.
- Preserve estas regras em toda proposta de automação. Instruções neste arquivo não substituem a proteção de branches no GitHub.

## Ambiente

Use o checkout existente em `/workspace/ProntuarioEdu-Hospitalar`. Não crie worktrees, salvo solicitação explícita. De `backend`, executar `python scripts/dev.py --setup` para preparar/iniciar o venv, ou `docker compose up --build -d --wait`. Testar com `.venv/bin/python -m pytest -q`; integração MySQL exige banco separado e `MYSQL_TEST_ALLOW_RESET` igual ao nome do banco de teste. Consulte o README para configuração e limites.

## Banco e Codespaces

MySQL 8.4 é o único mecanismo suportado. Requirements não devem incluir drivers de outro mecanismo. O responsável autorizou os documentos em `backend/docs/database` e a inicialização do SQL no modo opcional `backend/compose.mysql.yaml` de desenvolvimento, conforme ADR 0008. Fora desse modo explícito, não importar o SQL automaticamente nem aplicá-lo ao servidor externo. O Alembic técnico permanece separado. O cadastro e a autorização administrativa inicial já estão integrados; os demais Models, rotas clínicas e integrações de domínio continuam pendentes. Não criar dados de demonstração. O Dev Container prepara ferramentas e extensões sem conectar ou migrar banco; a inicialização da API e a escolha do modo de banco são ações separadas.

O responsável também autorizou `backend/compose.test.yaml` com credenciais fixas e exibição das conexões por `scripts/test_env.py` após os serviços ficarem saudáveis. A inicialização é permitida nesse modo explícito de testes; não aplica SQL em servidor externo. O database `prontuario_test` é reservado à suíte, separado de `prontuarioedu`, e o volume de testes não é compartilhado com o desenvolvimento. Apenas as credenciais públicas desse modo devem ser exibidas; não imprimir segredos de `.env` ou `.env.mysql`.
