# Contratos HTTP e validação

As Views Pydantic descrevem os dados aceitos e os campos públicos das respostas. Rotas usam esses contratos para validar chamadas e gerar OpenAPI; Controllers coordenam a operação e Models consultam o MySQL. A validação acontece antes de executar a lógica da operação. Autenticação e autorização continuam obrigatórias nas rotas protegidas.

## Entradas da autenticação

| Contrato | Campos e limites |
| --- | --- |
| `LoginRequest` | Formulário URL-encoded: `grant_type=password`, `username` de 1 a 150 caracteres e `password` de 1 a 128; `scope` opcional, até 512 |
| `RefreshRequest` | JSON: `refresh_token` de 1 a 200 caracteres e `scope` opcional, até 512; padrão `identity:read` |
| `PasswordChangeRequest` | JSON: `current_password` de 1 a 128 caracteres e `new_password` de 12 a 128 |

Campos desconhecidos são recusados. Um campo como `admin`, `user_id` ou `role` não pode ser adicionado à requisição para definir identidade ou conceder permissões. Os limites de entrada não substituem a verificação da senha, do token ou das concessões no banco.

O formulário de login aceita `client_id` e `client_secret` somente vazios, para compatibilidade com a interface Swagger. Campo repetido, UTF-8 inválido, formulário incompleto, tipo de concessão diferente ou campo não suportado recebe **400**. O tipo de conteúdo deve ser `application/x-www-form-urlencoded` (aceita variações de maiúsculas/minúsculas e parâmetro de charset); enviar JSON ao login recebe **415**.

JSON malformado, campo obrigatório ausente, tipo/tamanho inválido ou propriedade extra nas entradas JSON recebe **422**. Credenciais ou sessão inválidas continuam recebendo **401**. Uma mudança relevante para os clientes é que login estruturalmente inválido recebe 400; uma credencial com formato válido, mas incorreta, recebe 401. Consulte as rotas e o fluxo de tokens em [autenticação](AUTHENTICATION.md).

## Respostas e campos públicos

- `IdentityResponse` e `AdministratorResponse` usam UUID para os identificadores. No JSON eles continuam sendo strings, declaradas como `format: uuid` no OpenAPI.
- `HealthResponse` representa somente o sucesso: `status=ok` e `database=ok`. Indisponibilidade usa a resposta de erro 503.
- `TokenResponse` exige `expires_in` positivo e mantém `token_type=bearer`.
- `SessionResponse` contém identidade, expiração e indicação de renovação, sem retornar tokens.

As rotas mantêm `response_model` para filtrar dados segundo a View. Não retorne Models completos do banco nem campos como hash de senha. Falha na validação da resposta do servidor resulta em 500 sanitizado, sem devolver o objeto inválido ou valores privados.

## Envelope de erro da aplicação

Handlers e middleware compartilham `views/errors.py::error_body`, que produz `ErrorResponse`. Os códigos existentes foram mantidos.

| Campo | Significado |
| --- | --- |
| `error.code` | Código estável para tratamento pelo cliente |
| `error.request_id` | UUID da requisição, igual ao header `X-Request-ID` |
| `error.message` | Mensagem textual opcional; não contém corpo, tokens, SQL ou exceções internas |

Erros de validação não incluem os valores recebidos. Detalhes HTTP que não sejam mensagens textuais são substituídos por mensagem genérica, preservando o código de status. Ao criar novos Controllers, use mensagens públicas estáticas; não passe `str(exception)`, credenciais ou registros em `HTTPException.detail`.

| Situação | HTTP | `error.code` |
| --- | --- | --- |
| Formulário/requisição inválida | 400 | `http_400` |
| Credencial, token ou sessão inválida | 401 | `http_401` |
| Escopo/permissão insuficiente | 403 | `http_403` |
| Rota inexistente / método não aceito | 404 / 405 | `http_404` / `http_405` |
| Corpo acima do limite | 413 | `body_too_large` |
| Tipo de conteúdo não aceito | 415 | `http_415` |
| Validação JSON/query | 422 | `validation_error` |
| Limite de requisições excedido | 429 | `rate_limited` |
| Erro interno ou resposta inválida | 500 | `internal_error` |
| Dependência da operação indisponível | 503 | `http_503` |
| Limitador indisponível | 503 | `temporarily_unavailable` |

As respostas processadas pelo middleware incluem `Cache-Control: no-store`. Headers de protocolo são preservados, como `WWW-Authenticate`, `Allow` e `Retry-After`. O envelope é da aplicação: uma rejeição anterior às rotas, pelo gateway, validação do host ou CORS, pode usar a resposta própria dessa camada.

## Paginação para futuras listagens

O contrato reutilizável está em [`views/pagination.py`](src/prontuario_backend/views/pagination.py). Os endpoints atuais de identidade/saúde retornam objetos individuais; futuras listagens deverão adotar essa política.

| Parâmetro de query | Regra |
| --- | --- |
| `limit` | Padrão 20; mínimo 1 e máximo 100 |
| `offset` | Padrão 0; mínimo 0 e máximo 100.000 |

Valores fora dos limites recebem 422. A quantidade por página e o teto de offset limitam o custo das consultas; pesquisas muito profundas devem ser reduzidas por filtros do fluxo. Novos filtros devem ser declarados no DTO de query da listagem, que pode estender `PaginationParams`; parâmetros desconhecidos não são ignorados.

Use `Annotated[PaginationParams, Query()]` na entrada e `PageResponse[ItemResponse]` como `response_model`. `ItemResponse` deve ser a View dos campos públicos do recurso, não um dicionário livre nem uma entidade ORM. O parâmetro de tipo indica quais campos cada item pode conter. Nenhum endpoint de listagem foi criado nesta etapa.

O JSON paginado contém:

```json
{"items": [], "total": 0, "limit": 20, "offset": 0}
```

`total` é a contagem após os **mesmos filtros e autorizações** de `items`, antes de aplicar limit/offset. O Controller encaminha os parâmetros validados ao Model; o Model recebe valores simples, aplica autorização/filtros, ordenação e paginação, sem importar Views. Utilize uma ordenação fixa para o fluxo, com chave única de desempate, e uma leitura consistente entre contagem e itens.

Não calcule `total` sobre dados de outros usuários ou organizações. Página vazia, inclusive com offset além do total, é sucesso 200 com `items=[]`. O contrato recusa total negativo, mais itens que o limite e itens posicionados além do total informado.

## Testes e acompanhamento

Os testes unitários verificam os DTOs e os limites. Os testes de contrato usam requisições HTTP reais contra a aplicação em memória, com rotas temporárias exclusivas dos testes para paginação; não abrem banco nem criam dados na aplicação. A regressão do login é validada separadamente com MySQL descartável. Evidências e autorizações estão na [etapa 3 do F01](docs/F01.md).
