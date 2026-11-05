# Rotas: ligar URLs a Controllers

## Responsabilidade

Definem os caminhos, métodos HTTP e Controller responsável por cada operação.

## Como dividir o trabalho

Exemplo proposto: POST /api/v1/anotacoes aponta para o Controller de criação. Registrar autenticação comum, esquemas e metadados OpenAPI conforme o framework. Não executar a regra ou gravar no banco nesta pasta.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

A pasta ainda contém somente documentação. O framework e o banco não foram escolhidos.
