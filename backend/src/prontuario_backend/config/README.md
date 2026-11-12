# Configuração do servidor

## Responsabilidade

Centraliza leitura de configurações, inicialização da aplicação, conexão com banco e registro de rotas.

## Como dividir o trabalho

Validar variáveis necessárias sem imprimir segredos. Configurar autenticação, OpenAPI/Swagger e recursos do framework. Não definir regras do negócio. Migrações terão a localização padrão da ferramenta escolhida.

## Como validar

Cobrir a responsabilidade com testes: regras isoladas em `backend/tests/unit/`, comportamento HTTP e persistência em `backend/tests/integration/` e compatibilidade da API em `backend/tests/contract/`. Usar dados sintéticos.

O ambiente inicial usa FastAPI e SQLAlchemy/MySQL externo. Os arquivos Python desta pasta participam da API de desenvolvimento; funcionalidades clínicas ainda não foram implementadas.

`auth.py` contém `authenticate_request`, a função usada por `Security` para validar o access token e os escopos antes da execução do endpoint. Ela usa somente o emissor, audiência e JWKS configurados no servidor. Consulte o [guia de autenticação](../../../AUTHENTICATION.md) para configuração, validade e renovação no provedor externo.
