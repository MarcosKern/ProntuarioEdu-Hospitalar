# ADR 0006 — Dependências e melhorias operacionais

Status: melhorias solicitadas pelo responsável; mantém MVC e MySQL externo.

Separar dependências declaradas/locks de runtime e desenvolvimento. A imagem mantém apenas runtime; testes, lint, auditoria e geração de locks ficam no ambiente dev. Alembic e cryptography permanecem no runtime por serem utilizados na inicialização e ferramentas operacionais. Os locks preservam as versões de aplicação já testadas, enquanto as ferramentas de manutenção devem continuar compatíveis e sem vulnerabilidades conhecidas.

Adicionar timeouts SQL limitados e sem retry de escrita, schema de erros OpenAPI por operação, logs sanitizados de falha e health check no Dockerfile. Agendar auditoria semanal e atualizações por PR. Workflows usam Actions verificadas e fixadas por commit.

O workflow CodeQL está preparado; sua execução e integração com a configuração padrão/nativa precisam ser confirmadas no GitHub após publicação. A atualização do ruleset foi recusada por permissão; nenhuma proteção foi reduzida e o JSON preservando os gates é entregue ao administrador.
