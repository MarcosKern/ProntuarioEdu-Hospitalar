# Pacote do Back-end

## Responsabilidade

Organiza domínio, aplicação, adaptadores e composição.

## Divisão de competências

Domínio não importa outras camadas; aplicação importa domínio; adaptadores importam contratos da aplicação; bootstrap conecta os componentes.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
