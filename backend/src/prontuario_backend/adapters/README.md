# Adaptadores

## Responsabilidade

Tradução entre tecnologias externas e contratos da aplicação.

## Divisão de competências

Organizar por direção: inbound inicia casos de uso; outbound implementa capacidades solicitadas por eles. Não transferir regras de negócio para bibliotecas externas.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
