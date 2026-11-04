# Contratos públicos

- `openapi`: contrato HTTP versionado, após definição dos primeiros casos de uso.
- `examples`: exemplos sintéticos de requisições e respostas, sem dados de pacientes ou credenciais.

O contrato é a fronteira entre Back-end, Desktop, Web e integrações. Clientes compartilham esse contrato, não modelos de persistência ou regras internas do servidor. Mudanças incompatíveis exigem política de versionamento e migração. Evitar manter manualmente especificações e modelos duplicados; definir uma fonte de verdade na ADR do framework.
