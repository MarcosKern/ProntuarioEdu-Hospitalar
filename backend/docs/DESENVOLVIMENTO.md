# Desenvolver o backend

Para iniciar com Docker, use o [roteiro principal](../README.md). Este documento reúne o trabalho no código e a alternativa de executar a API diretamente no Python. A divisão MVC e o exemplo por pasta estão em [arquitetura](../../docs/architecture.md).

## Executar a API no Python

Use o venv de Python 3.12 preparado no roteiro principal e um MySQL autorizado com o schema necessário. Configure `backend/.env` conforme [MySQL externo](MYSQL.md#preparar-a-conexão) e a chave JWT conforme o roteiro de execução. O MySQL do modo Docker resolve `mysql` apenas entre contêineres: para Python no host, use a porta publicada no loopback e suas credenciais privadas. Não altere a configuração de um ambiente existente sem revisar o destino.

De `backend`:

```bash
.venv/bin/python scripts/dev.py
```

O comando aplica `alembic upgrade head` e depois inicia Uvicorn em `127.0.0.1:8000` com reload. Falha de migration impede startup. O terminal fica ocupado; Ctrl+C encerra. Não execute junto ao Compose na mesma porta. `--port 8001` muda a porta; `--setup` também instala `requirements-dev.txt` antes de aplicar migrations e iniciar.

No Codespace, a tarefa **Codespaces: iniciar API** ou, da raiz, `backend/.venv/bin/python .devcontainer/start.py`, acrescenta o hostname encaminhado exato ao processo local. Esse wrapper não configura o serviço Compose. Variáveis do processo têm precedência sobre `.env` neste modo.

Sem `REDIS_URL`, o limitador é em memória por processo, permitido apenas em desenvolvimento/testes. O Redis do Compose não está publicado para o Python no host. O cadastro administrativo continua sendo explícito: com a conexão correta, execute `.venv/bin/python scripts/create_admin.py`. As orientações de [uso do Swagger](../README.md#5-abrir-e-usar-o-swagger) são as mesmas.

## Criar uma rota protegida

[`routes/api.py`](../src/prontuario_backend/routes/api.py) é a referência executável. O exemplo abaixo ilustra a dependência que roda **antes** do corpo do endpoint:

```python
from typing import Annotated
from fastapi import APIRouter, Security
from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.views.auth import IdentityResponse

router = APIRouter()

@router.get(
    '/api/v1/minha-identidade',
    response_model=IdentityResponse,
    summary='Consultar minha identidade',
    description='Exige JWT, sessão ativa e escopo identity:read.',
    operation_id='get_my_identity',
    tags=['Autenticação'],
)
def my_identity(
    user: Annotated[AuthenticatedUser, Security(authenticate_request, scopes=['identity:read'])],
):
    return IdentityResponse(subject=user.subject)
```

Não copie uma segunda versão das rotas já existentes. Para uma operação nova, registre o router, declare os erros compartilhados de `views/errors.py` e teste o contrato. `response_model` filtra a saída; `summary`, `description`, `operation_id` único e `responses` alimentam o OpenAPI. Documentar um erro não implementa seu tratamento.

O usuário vem da dependência, nunca de um campo confiado ao cliente. Para dados clínicos, exija também autorização sobre o registro, como `require_record_access`, e as regras de negócio aprovadas. Consulte [autenticação](AUTENTICACAO.md#proteger-novos-endpoints) e [contratos HTTP](CONTRATOS.md).

## Sessões e transações

`config/database.py::session()` fornece uma sessão SQLAlchemy. `with session() as db` fecha a sessão, mas exige `db.commit()` explícito. `with session() as db, db.begin():` confirma na saída normal e desfaz em exceções. Se capturar falha de flush e reutilizar a sessão, execute `db.rollback()` antes.

Nos Models com SQL direto, `with engine().begin() as connection` confirma ou desfaz a unidade inteira; `with engine().connect() as connection` serve para leitura. Os contextos devolvem conexões ao pool. Não responda sucesso antes do commit. DDL MySQL pode provocar commits implícitos; rollback de sessão não desfaz automaticamente mudanças de schema.

Models concentram consultas e regras sem importar Controllers/Views. Controllers coordenam o fluxo e a autorização; Views Pydantic selecionam entradas/saídas públicas sem consultar banco. `models/users.py` integra cadastro/sessões; `controllers/auth.py` coordena login, refresh, logout e senha; `controllers/admin.py` verifica concessões administrativas. As migrations técnicas são separadas do SQL de domínio.

## Manter dependências

`requirements.in` declara dependências diretas; `requirements.txt` fixa o runtime da imagem. `requirements-dev.in` acrescenta testes, lint e auditoria; `requirements-dev.txt` fixa o conjunto de desenvolvimento. Não use `pip freeze` para substituir os locks e misturar ambientes.

Depois de uma alteração intencional nos arquivos `.in`, com aprovação aplicável e de `backend`:

```bash
.venv/bin/python -m piptools compile --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file requirements.txt requirements.in
.venv/bin/python -m piptools compile --allow-unsafe --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file requirements-dev.txt requirements-dev.in
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
```

Revise as diferenças, execute [testes e auditorias](../tests/README.md) e reconstrua a imagem. Código, requirements, migrations e SQL devem ter alterações de comportamento revisadas separadamente de reorganizações documentais.
