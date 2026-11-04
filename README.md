# ProntuarioEdu-Hospitalar

Estrutura inicial para Back-end Python, Desktop Python e Web responsiva com tecnologia em aberto.

| Diretório | Responsabilidade |
| --- | --- |
| [backend](backend/README.md) | API compartilhada e regras de negócio |
| [desktop](desktop/README.md) | Aplicativo Python que consome a API |
| [web](web/README.md) | Interface compatível com desktop e dispositivos móveis |
| [contracts](contracts/README.md) | Contratos públicos entre servidor e clientes |
| [infra](infra/README.md) | Desenvolvimento e implantação futuros |
| [docs](docs/architecture.md) | Arquitetura, decisões e governança |

A proposta é um monólito modular com arquitetura hexagonal no servidor. Consulte a [ADR inicial](docs/adr/0001-arquitetura-inicial.md), pendente de aprovação, e as [alternativas](docs/architecture-options.md).

Esta etapa contém apenas organização e documentação. Ainda não há dependências de aplicação, comandos de execução ou testes implementados. Frameworks, banco, toolkit Desktop e autenticação dependem da validação da arquitetura.
