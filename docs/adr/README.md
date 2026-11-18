# Decisões arquiteturais

ADRs registram contexto, alternativas, decisão, consequências e aprovação. São histórico de decisões, não roteiros de instalação. O estado atual e a organização do código estão em [arquitetura](../architecture.md); a execução, no [roteiro do backend](../../backend/README.md).

| Registro | Assunto |
| --- | --- |
| [0001](0001-arquitetura-inicial.md) | MVC e limites dos componentes |
| [0002](0002-ambiente-desenvolvimento.md) | Ambiente inicial |
| [0003](0003-seguranca-operacao.md) | Segurança e operação |
| [0004](0004-mysql-externo.md) | MySQL externo |
| [0005](0005-correcoes-revisao.md) | Correções após revisão |
| [0006](0006-dependencias-e-operacao.md) | Separação de dependências e operação |
| [0007](0007-codespaces-e-ambiente-mysql.md) | Codespaces e escolhas de ambiente |
| [0008](0008-mysql-container-desenvolvimento.md) | MySQL opcional em contêiner |
| [0009](0009-administrador-aplicacao-keycloak.md) | Administrador externo; substituída pela 0010 |
| [0010](0010-autenticacao-local.md) | Login local/JWT atual, substituindo as decisões anteriores de identidade |

Para nova decisão, use numeração sequencial e explicite se é proposta, aprovada ou substituída. Referencie a ADR afetada e obtenha a validação aplicável antes de introduzir arquitetura ou dependências. Não apague uma decisão antiga só porque foi substituída.
