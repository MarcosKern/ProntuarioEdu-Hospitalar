# ADR 0001 — Organização inicial e comunicação entre aplicativos

Status: proposta; pendente de aprovação explícita da arquitetura.

## Contexto

Back-end e Desktop usam Python. Web será responsiva, com tecnologia em aberto. A API deve atender também futuros aplicativos. A solicitação atual autoriza criar a organização de pastas; não resolve escolhas de frameworks, banco, toolkit ou operação offline.

## Proposta

Adotar um monorepositório com `backend`, `desktop`, `web`, `contracts`, `infra` e `docs`. No servidor, usar monólito modular com arquitetura hexagonal: domínio independente, casos de uso, portas e adaptadores. No Desktop, separar apresentação, coordenação dos fluxos e comunicação HTTP. Preservar a organização nativa do framework Web quando escolhido.

Web, Desktop e integrações acessam o servidor por HTTPS e API REST versionada documentada com OpenAPI. Apenas o servidor acessa a persistência. Banco, autenticação e transporte são adaptadores; regras de negócio não dependem deles. O diretório `bootstrap` compõe as implementações concretas.

## Alternativas

- Django + DRF em organização modular: adequado quando administração e funcionalidades integradas forem prioritárias; pode manter os limites propostos.
- FastAPI: candidato quando o foco principal for uma API; não é dependência instalada.
- Microsserviços: adiar até haver justificativa de escala, isolamento ou autonomia das equipes; introduzem consistência e operação distribuídas.

## Contratos e segurança

Definir fonte de verdade do OpenAPI, erros padronizados, paginação e compatibilidade antes da primeira API. Aplicar autorização no servidor. Avaliar OIDC/OAuth2 e PKCE para clientes públicos e sessão segura para Web, sem segredos embutidos nos clientes. Definir auditoria, proteção de dados sensíveis, retenção, backup e recuperação conforme os requisitos reais. Exemplos e testes devem usar dados sintéticos.

## Estratégia de testes

Domínio e casos de uso terão testes unitários; adaptadores terão testes de integração com serviços de teste; API terá testes de contrato; clientes terão testes de fluxos e integração. Avaliar testes de ponta a ponta e acessibilidade para os fluxos principais. As pastas presentes são reservas: nenhum teste foi implementado ou executado nesta etapa.

## Consequências

Uma API central permite vários clientes e mantém regras no servidor. Limites de importação precisam ser revisados e futuramente verificados por automação. Não compartilhar modelos de banco com clientes. Desktop offline exige ADR própria para sincronização, conflitos e dados locais.

## Aprovação pendente

O responsável deve aprovar ou revisar a proposta e escolher framework Python, persistência, toolkit Desktop, autenticação e necessidade de offline. A tecnologia Web permanece em aberto. Até a aprovação, a estrutura é um esqueleto documental sem lógica de aplicação ou dependências.
