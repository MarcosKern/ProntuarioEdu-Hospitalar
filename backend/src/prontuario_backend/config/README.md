# Configuração do servidor

## Responsabilidade

Centraliza leitura de configurações, inicialização da aplicação, conexão com banco e registro de rotas.

## Como dividir o trabalho

Validar variáveis necessárias sem imprimir segredos. Configurar autenticação, OpenAPI/Swagger e recursos do framework. Não definir regras do negócio. Migrações terão a localização padrão da ferramenta escolhida.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

A pasta ainda contém somente documentação. O framework e o banco não foram escolhidos.
