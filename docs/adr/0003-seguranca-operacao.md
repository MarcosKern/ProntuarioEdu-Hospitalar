# ADR 0003 — Segurança e operação do Back-end MVC

> Histórico: a escolha de banco deste documento foi substituída pela [ADR 0004 — MySQL externo](0004-mysql-externo.md).

Status: implementação solicitada pelo responsável. Sem cadastros, prontuários ou concessões iniciais.

## Decisões

Configuração validada por ambiente; PostgreSQL com Alembic para evolução do schema; SQLite preservado para testes/desenvolvimento sem serviços; Redis para limites distribuídos. O ambiente de produção exige PostgreSQL, Redis e configuração OIDC completa e HTTPS, desabilita Swagger/schema e métricas públicas. OIDC permanece externo: não existem credenciais ou usuários padrão.

Models técnicos armazenam permissões explícitas por subject, registro e ação, e eventos de auditoria. O Controller de autorização nega por padrão e grava decisão em auditoria antes de liberar. Não há endpoint de cadastro de permissões nem de conteúdo clínico: as políticas e perfis reais ainda precisam ser definidos. Futuras operações devem chamar o controle antes de acessar dados e registrar também a conclusão da alteração na mesma transação do negócio. Uma autorização concedida não equivale a alteração concluída.

Logs HTTP contêm apenas rota parametrizada, método, status, duração e identificador gerado pelo servidor. Não incluir query string, corpos, tokens, identificadores de pacientes ou exceções SQL. Auditoria contém identificadores pessoais e exige acesso restrito e política de retenção.

## Limites e consequências

O trigger PostgreSQL rejeita UPDATE/DELETE de auditoria para operações comuns; não protege contra dono/superusuário capaz de desabilitá-lo. Produção precisa separar usuário de migração e runtime e restringir acesso operacional. TLS de entrada, certificados, TLS/autenticação de Redis/PostgreSQL, retenção e monitoramento privado dependem da infraestrutura real. Compose é desenvolvimento; não deve ser publicado diretamente.

A configuração CI executa testes, análise estática, auditoria de dependências e scan da imagem/segredos. Arquivo de workflow não prova execução ou ativação de proteção de branches. Não há dados de aplicação inseridos por migração; fixtures só existem em bancos temporários ou transações revertidas de teste.
