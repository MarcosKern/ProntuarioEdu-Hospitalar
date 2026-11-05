# Ambiente de desenvolvimento

## Responsabilidade

Configurações futuras de serviços locais e comandos reproduzíveis.

## Divisão de competências

Escolher serviços somente após a arquitetura aprovada. Documentar portas, prontidão e limpeza de dados de teste; não incluir segredos nem assumir que processos sobrevivem à restauração do ambiente.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
