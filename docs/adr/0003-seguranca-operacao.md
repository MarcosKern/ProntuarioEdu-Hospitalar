# ADR 0003 — Segurança e operação do Back-end MVC

Atualização de 12/11/2026: as decisões de autenticação abaixo foram substituídas pelo [login local da ADR 0010](0010-autenticacao-local.md); os demais controles de segurança permanecem.

> Histórico: a escolha de banco deste documento foi substituída pela [ADR 0004 — MySQL externo](0004-mysql-externo.md).

Status: implementação solicitada pelo responsável. Sem cadastros, prontuários ou concessões iniciais.

## Decisões

Configuração validada por ambiente; MySQL com Alembic para evolução do schema; testes usam MySQL isolado; Redis para limites distribuídos. O ambiente de produção exige MySQL, Redis e configuração OIDC completa e HTTPS, desabilita Swagger/schema e métricas públicas. OIDC permanece externo: não existem credenciais ou usuários padrão.

Por solicitação do responsável, a função `authenticate_request` valida cada requisição antes da execução dos endpoints protegidos, incluindo os escopos OAuth2 declarados na rota. O escopo técnico `identity:read` protege a consulta da própria identidade e da validade do acesso. A consulta `GET /api/v1/auth/session` informa expiração e necessidade de renovação; o cliente realiza a renovação no provedor externo. Isso mantém o fluxo OIDC escolhido e a divisão MVC, sem adicionar dependências, emitir tokens locais ou alterar o banco. Consulte o [contrato e os testes de autenticação](../../backend/AUTHENTICATION.md).

Models técnicos armazenam permissões explícitas por subject, registro e ação, e eventos de auditoria. O Controller de autorização nega por padrão e grava decisão em auditoria antes de liberar. Não há endpoint de cadastro de permissões nem de conteúdo clínico: as políticas e perfis reais ainda precisam ser definidos. Futuras operações devem chamar o controle antes de acessar dados e registrar também a conclusão da alteração na mesma transação do negócio. Uma autorização concedida não equivale a alteração concluída.

Logs HTTP contêm apenas rota parametrizada, método, status, duração e identificador gerado pelo servidor. Não incluir query string, corpos, tokens, identificadores de pacientes ou exceções SQL. Auditoria contém identificadores pessoais e exige acesso restrito e política de retenção.

## Limites e consequências

O trigger MySQL rejeita UPDATE/DELETE de auditoria para operações comuns; não protege contra dono/superusuário capaz de desabilitá-lo. Produção precisa separar usuário de migração e runtime e restringir acesso operacional. TLS de entrada, certificados, TLS/autenticação de Redis/MySQL, retenção e monitoramento privado dependem da infraestrutura real. Compose é desenvolvimento; não deve ser publicado diretamente.

A configuração CI executa testes, análise estática, auditoria de dependências e scan da imagem/segredos. Arquivo de workflow não prova execução ou ativação de proteção de branches. Não há dados de aplicação inseridos por migração; fixtures só existem em bancos temporários ou transações revertidas de teste.
