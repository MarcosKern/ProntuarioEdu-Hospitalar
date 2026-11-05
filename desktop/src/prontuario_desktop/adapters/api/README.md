# Cliente HTTP Desktop

## Responsabilidade

URLs, serialização, transporte HTTPS, envio da sessão e interpretação das respostas.

## Divisão de competências

Implementar timeout e erros de conexão. Não repetir operações de escrita cegamente. Não guardar segredos de aplicação no executável nem registrar tokens ou dados sensíveis.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
