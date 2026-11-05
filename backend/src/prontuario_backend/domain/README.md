# Domínio

## Responsabilidade

Entidades, objetos de valor e invariantes do negócio, independentes de framework.

## Divisão de competências

Uma regra válida em qualquer interface pertence aqui. Não receber Request, sessão SQL ou objetos de interface. Separar futuramente subpacotes por capacidade de negócio aprovada.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
