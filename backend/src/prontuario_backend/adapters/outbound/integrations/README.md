# Integrações externas

## Responsabilidade

Clientes de serviços externos que implementam portas da aplicação.

## Divisão de competências

Definir timeout, tradução de erros e política de repetição. Repetir escritas apenas quando houver garantia de idempotência. Não espalhar SDKs ou credenciais pela aplicação.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
