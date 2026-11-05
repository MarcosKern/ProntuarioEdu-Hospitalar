# Contratos públicos

- `openapi`: contrato HTTP versionado, após definição dos primeiros casos de uso.
- `examples`: exemplos sintéticos de requisições e respostas, sem dados de pacientes ou credenciais.

O contrato é a fronteira entre Back-end, Desktop, Web e integrações. Clientes compartilham esse contrato, não modelos de persistência ou regras internas do servidor. Mudanças incompatíveis exigem política de versionamento e migração. Evitar manter manualmente especificações e modelos duplicados; definir uma fonte de verdade na ADR do framework.

## Divisão de competências e fluxo de mudança

O Back-end define e implementa o comportamento; responsáveis pelos clientes revisam a facilidade de consumo e a compatibilidade; testes verificam a concordância. O contrato não pertence exclusivamente à interface visual ou ao banco.

1. Definir operação, entradas, erros e requisitos de segurança com exemplos sintéticos.
2. Atualizar a fonte de verdade do OpenAPI escolhida na ADR do framework.
3. Gerar/validar o contrato e revisar impacto em clientes existentes.
4. Implementar e testar o servidor contra o contrato.
5. Atualizar clientes conforme a estratégia de compatibilidade, sem quebrar versões já distribuídas do Desktop.

`openapi/` cuida da descrição formal; `examples/` explica casos concretos. Swagger UI apenas apresenta a especificação e permite requisições reais. Esquemas de persistência não devem ser publicados como contrato por conveniência.
