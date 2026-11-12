# Decisões arquiteturais

## Responsabilidade

Registro de contexto, alternativas, decisão, consequências e aprovação.

## Divisão de competências

Usar arquivos numerados. Distinguir proposta, aprovação e substituição. Uma mudança de arquitetura deve referenciar a decisão afetada, sem apresentar proposta como implementação aprovada.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

A [ADR 0010](0010-autenticacao-local.md) registra o login local atual e substitui as decisões anteriores de autenticação. ADRs históricas mantêm seu contexto, com aviso de substituição.
