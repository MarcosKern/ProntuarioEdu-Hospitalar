# Aplicação e portas

## Responsabilidade

Casos de uso, entradas e saídas da aplicação e interfaces para persistência e serviços externos.

## Divisão de competências

Coordenar autorização contextual, regras de domínio e limites de transação. Depender de portas, nunca de implementações SQL ou HTTP. DTOs da aplicação não são modelos de banco.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
