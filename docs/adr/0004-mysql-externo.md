# ADR 0004 — MySQL externo como padrão do projeto

Status: solicitado pelo responsável; substitui as escolhas de banco das ADRs 0002 e 0003.

Usar MySQL 8.4 com SQLAlchemy/PyMySQL em desenvolvimento e produção. DATABASE_URL é obrigatória, sem fallback ou criação automática de arquivo local. O Compose da aplicação não inicia banco: recebe a conexão do servidor externo.

Testes de integração usam um MySQL descartável separado, nunca o banco real. A CI cria seu serviço MySQL isolado. Nenhuma migração insere usuários, registros ou permissões.

A revisão 0001 mantém as mesmas instruções de criação de tabelas MySQL; o ramo legado de outro dialeto foi removido sem alterar o resultado no MySQL; a revisão 0002 adiciona triggers MySQL contra UPDATE/DELETE de auditoria e comparação sensível a maiúsculas para subjects de identidade. As datas são gravadas em UTC, com sessão MySQL em UTC. Banco existente de outro mecanismo exige migração de dados planejada, não troca automática de URL nem reutilização da tabela alembic_version.

Credenciais, hostname, acesso de rede e CA confiável do servidor real precisam ser configurados externamente. Não se presume autorização para executar DDL no banco real. Alembic deve ser executado pelo responsável com credenciais de migração antes de liberar a API; usuário de runtime deve ter privilégios mínimos.
