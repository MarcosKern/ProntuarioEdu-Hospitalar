# Índice da documentação

Para executar o projeto, comece no [roteiro único do backend](../backend/README.md). Cada assunto abaixo tem um documento responsável; novos guias devem apontar para ele, em vez de copiar comandos de instalação e subida.

| Assunto | Fonte principal |
| --- | --- |
| Docker, administrador inicial, Swagger, logs e parada | [Backend](../backend/README.md) |
| Preparação/reconstrução do editor remoto | [Codespaces](../.devcontainer/README.md) |
| MVC, disposição das pastas e competências | [Arquitetura](architecture.md) |
| Desenvolvimento Python, endpoint documentado e dependências | [Desenvolvimento](../backend/docs/DESENVOLVIMENTO.md) |
| Banco descartável, pytest e CI | [Testes](../backend/tests/README.md) |
| Tokens, sessões e administrador existente | [Autenticação](../backend/docs/AUTENTICACAO.md) |
| MySQL externo, TLS, migrations e backup | [MySQL](../backend/docs/MYSQL.md) |
| DTOs, validação, erros HTTP e paginação | [Contratos HTTP](../backend/docs/CONTRATOS.md) |
| Controles de segurança e operação | [Segurança](../backend/docs/SEGURANCA.md) |
| Modelo físico, dicionário e SQL | [Banco de domínio](../backend/docs/database/README.md) |
| Exportação OpenAPI e compatibilidade dos clientes | [Contratos públicos](../contracts/README.md) |
| Hospedagem e limites da implantação atual | [Infraestrutura](../infra/README.md) |
| Clientes ainda em desenvolvimento | [Desktop](../desktop/README.md) e [Web](../web/README.md) |
| Motivos e aprovações das decisões | [ADRs](adr/README.md) |
| Revisão, permissões e merge | [Governança](repository-governance.md) |

## Histórico

O [registro do card F01](historico/F01.md) conserva evidências e resultados datados. Ele não é um guia de instalação nem comprova o estado atual dos checks no GitHub. As ADRs preservam decisões substituídas com o contexto de sua época.

## Manter a documentação

Ao mudar uma funcionalidade, atualize seu documento responsável e os links afetados. Comandos executáveis precisam informar diretório, pré-requisitos, resultado esperado e efeito nos dados. Não inclua segredos ou registros reais nos exemplos. Propostas de produto e arquitetura precisam de aprovação própria; exemplos didáticos não homologam regras clínicas.
