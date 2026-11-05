# Controllers: coordenar a requisição

## Responsabilidade

Recebem a chamada encaminhada pelas rotas e coordenam a operação.

## Como dividir o trabalho

Verificar a identidade autenticada e a autorização sobre o registro, validar os dados de entrada, chamar o Model e selecionar a resposta da View. Não concentrar regras de negócio ou SQL aqui. Não confiar em autor ou permissões enviados no JSON.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

A pasta ainda contém somente documentação. O framework e o banco não foram escolhidos.
