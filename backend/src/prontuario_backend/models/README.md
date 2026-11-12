# Models: dados e regras

## Responsabilidade

`users.py` consulta o cadastro administrativo existente no schema MySQL e oferece o bootstrap explícito da primeira conta. Não cria tabelas, pacientes ou profissionais e não reativa concessões revogadas. O cadastro persiste apenas o hash scrypt da senha. As sessões guardam hash do refresh token, expiração e revogação.

Representam os dados do sistema, suas regras de validade e operações de persistência usando o banco/ORM que for escolhido.

## Como dividir o trabalho

Aqui entram entidades, validações de negócio e consultas. Não receber objetos HTTP nem montar respostas JSON. Exemplo futuro: Anotacao.criar valida o texto e salva o registro dentro de uma transação. Não importar controllers ou views.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

O ambiente inicial usa FastAPI e SQLAlchemy/MySQL externo. Os arquivos Python desta pasta participam da API de desenvolvimento; funcionalidades clínicas ainda não foram implementadas.
