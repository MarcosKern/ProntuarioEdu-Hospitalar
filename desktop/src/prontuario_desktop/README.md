# Pacote do Desktop

## Responsabilidade

Apresentação, fluxos locais, adaptadores e bootstrap.

## Divisão de competências

A apresentação chama a aplicação local; esta depende de uma porta de API; o adaptador HTTP implementa a porta e o bootstrap conecta tudo.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
