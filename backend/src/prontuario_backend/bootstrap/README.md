# Composição do servidor

## Responsabilidade

Criação da aplicação, leitura validada de configuração e conexão entre portas e adaptadores.

## Divisão de competências

Instanciar repositórios e casos de uso, registrar rotas e gerenciar recursos. Não decidir regras de negócio. Segredos vêm do ambiente seguro, sem valores no código ou nos logs.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
