# ADR 0005 — Correções da revisão de segurança

Status: correções solicitadas pelo responsável. Sem alteração da arquitetura MVC ou inserção de dados na aplicação.

Subjects OIDC são comparados exatamente com collation MySQL NO PAD, por nova migração e metadados correspondentes. Produção exige CA de MySQL e Redis TLS com verificação de hostname/certificado. Desenvolvimento mantém os modos documentados sem TLS quando autorizados na rede local.

O Redis tem timeouts positivos limitados e nenhuma repetição automática no limitador. Falha retorna 503, sem liberar acesso. Erros HTTP do framework passam pelo contrato JSON comum preservando headers de autenticação e método permitido.

Limpeza de testes exige nome de banco explícito, confirmação por variável e comparação com os destinos de aplicação, sem considerar diferenças de credencial como isolamento. Nenhum DDL de limpeza acontece antes da validação. DNS alternativos ainda exigem cuidado do operador; testes devem usar banco dedicado e credenciais restritas a ele.

Governança local é preparada para versionamento. O ruleset remoto continua dependendo de escrita administrativa da integração; o arquivo JSON é entregue para aplicação por administrador, sem registrar checks inexistentes.
