# API HTTP e Swagger

## Responsabilidade

Rotas, esquemas HTTP, extração da identidade autenticada, serialização e tradução de erros.

## Divisão de competências

Validar formato e tamanho das entradas; autenticar com o mecanismo aprovado; passar a identidade confiável à aplicação. Não aceitar papel/permissão enviados pelo cliente como prova. Mapear erros conhecidos para respostas documentadas e gerar OpenAPI/Swagger. Não executar SQL nem decidir regras de domínio aqui.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
