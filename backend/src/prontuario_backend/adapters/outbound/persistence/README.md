# Persistência

## Responsabilidade

Repositórios, mapeamento de entidades, consultas e implementação da unidade de trabalho, quando definida.

## Divisão de competências

Conhece ORM/SQL e transações concretas. A aplicação define o limite atômico; este adaptador o realiza. Isolar migrações na localização indicada pelo framework escolhido. Não retornar modelos ORM ao domínio ou ao cliente.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
