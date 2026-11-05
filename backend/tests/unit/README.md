# Testes unitários do servidor

## Responsabilidade

Regras de domínio e casos de uso, com adaptadores falsos nas portas.

## Divisão de competências

Não requerer rede, banco real ou servidor HTTP. Cobrir sucesso, rejeição de regra e falta de autorização; verificar que rejeições não produzem gravações.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
