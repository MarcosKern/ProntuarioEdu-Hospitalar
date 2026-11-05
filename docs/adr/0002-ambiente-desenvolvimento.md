# ADR 0002 — Ambiente inicial do Back-end

> Histórico: a escolha de banco deste documento foi substituída pela [ADR 0004 — MySQL externo](0004-mysql-externo.md).

Status: implementado para atender à solicitação de SQL, Swagger, venv, OAuth2 e execução em desenvolvimento. A configuração de um provedor real continua pendente.

## Decisão e justificativa

Usar Python 3.12, FastAPI (API e Swagger integrados), SQLAlchemy com SQLite local, Uvicorn, PyJWT/cryptography para JWT RS256 e pytest/httpx. São escolhas mínimas para executar o MVC sem instalar um servidor de banco adicional. `venv` é módulo padrão do Python, não dependência pip. “auth2” foi interpretado como OAuth2.

OAuth2 Authorization Code com PKCE é apresentado no Swagger; o Back-end valida tokens emitidos por provedor OIDC externo usando JWKS, issuer e audience configurados. Não emitir tokens locais nem criar credenciais de teste na aplicação. Acesso protegido falha quando a configuração está ausente.

## Limites

SQLite serve ao desenvolvimento; banco de produção, migrações, autorização por registro, recursos clínicos e provedor real não estão implementados. O endpoint de saúde executa SELECT 1 e o endpoint protegido demonstra identidade. O exemplo clínico no README é apenas didático.

Docker usa imagem Python, execução não root, volume de dados e código montado para reload no Compose. O freeze inclui ferramentas de teste e é destinado ao desenvolvimento. Imagem/base e versões devem ser revisadas periodicamente; o teste do provedor externo exige configuração de acesso e cliente próprios.

## Verificação

Testes locais cobrem SQL, schema Swagger/OpenAPI e validação de tokens com chaves sintéticas. Build Docker e execução do Compose são verificados separadamente; não equivalem a validação de login em um provedor real.
