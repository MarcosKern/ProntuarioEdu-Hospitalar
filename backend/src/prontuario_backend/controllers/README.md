# Controllers: coordenar a requisição

## Responsabilidade

`admin.py::require_system_admin` exige identidade e escopos verificados e confirma o usuário/perfil/permissão no banco da aplicação antes de autorizar uma operação administrativa.

Recebem a chamada encaminhada pelas rotas e coordenam a operação.

## Como dividir o trabalho

Verificar a identidade autenticada e a autorização sobre o registro, validar os dados de entrada, chamar o Model e selecionar a resposta da View. Não concentrar regras de negócio ou SQL aqui. Não confiar em autor ou permissões enviados no JSON.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

O ambiente inicial usa FastAPI e SQLAlchemy/MySQL externo. Os arquivos Python desta pasta participam da API de desenvolvimento; funcionalidades clínicas ainda não foram implementadas.

`auth.py::session_status` recebe uma identidade já autenticada, calcula o tempo restante do access token e seleciona a resposta de validade da sessão. A autenticação da requisição acontece antes, em `config/auth.py`; a renovação de tokens pertence ao provedor OAuth2/OIDC externo.
