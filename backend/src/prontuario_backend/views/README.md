# Views: apresentar respostas da API

## Responsabilidade

Transformam resultados e erros conhecidos em respostas HTTP/JSON.

## Como dividir o trabalho

Em uma API, View é a representação dos dados, não uma tela HTML. Selecionar campos públicos, padronizar erros e evitar expor modelos completos, tokens ou dados indevidos. Não consultar banco nem alterar regras. Desktop e Web constroem suas próprias telas.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

O ambiente inicial usa FastAPI e SQLAlchemy/SQLite. Os arquivos Python desta pasta participam da API de desenvolvimento; funcionalidades clínicas ainda não foram implementadas.
