# Infraestrutura

O ambiente de desenvolvimento executável está em `backend`, não nesta pasta:

- [README do Back-end](../backend/README.md#configurar-o-ambiente-de-desenvolvimento): instalação local e Docker.
- [MySQL externo](../backend/MYSQL.md): conexão, TLS, migrações, testes e backups.
- [Segurança e operação](../backend/SECURITY.md): limites, auditoria e requisitos de produção.
- [Compose](../backend/compose.yaml): API e Redis privados, sem servidor de banco local.
- [Override TLS](../backend/compose.tls.yaml): montagem da CA MySQL.

`development/` e `deployment/` reservam espaço para infraestrutura adicional futura. Não há implantação de produção automatizada nesta pasta. Docker Engine/Desktop e Compose precisam estar funcionando; não iniciar um segundo daemon dentro de ambiente gerenciado.

## Divisão de competências

Infraestrutura cuida de configuração, conectividade, recursos, disponibilidade e recuperação. Back-end informa dependências, migrações e verificações funcionais. Os clientes usam somente a API. Segredos ficam fora do repositório; permissões e autorização são verificadas no servidor.
