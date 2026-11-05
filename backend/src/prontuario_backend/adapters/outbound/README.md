# Saídas do servidor

## Responsabilidade

Implementações concretas das portas da aplicação.

## Divisão de competências

Persistência e integrações ficam separadas. Falhas técnicas devem ser traduzidas para erros definidos na fronteira, sem expor detalhes sensíveis.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
