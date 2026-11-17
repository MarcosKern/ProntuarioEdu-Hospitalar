from typing import Annotated

from fastapi import APIRouter, Depends, Response, Security

from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.controllers.admin import require_system_admin
from prontuario_backend.controllers.auth import (
    logout,
    refresh_access,
    session_status,
    token_endpoint,
    update_password,
)
from prontuario_backend.controllers.health import health
from prontuario_backend.views.auth import (
    AdministratorResponse,
    IdentityResponse,
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    SessionResponse,
    TokenResponse,
)
from prontuario_backend.views.errors import ERROR_RESPONSES
from prontuario_backend.views.health import HealthResponse

router = APIRouter()
AUTH_ERRORS = {
    status: ERROR_RESPONSES[status]
    for status in (400, 401, 403, 405, 413, 415, 422, 429, 500, 503)
}
router.add_api_route(
    "/api/v1/auth/token",
    token_endpoint,
    methods=["POST"],
    response_model=TokenResponse,
    responses=AUTH_ERRORS,
    tags=["Autenticação"],
    summary="Entrar com usuário e senha",
    operation_id="login",
    description="Formulário com grant_type=password, username, password e scope. Sem cadastro automático.",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": LoginRequest.model_json_schema()
                }
            },
        }
    },
)
router.add_api_route(
    "/health",
    health,
    methods=["GET"],
    response_model=HealthResponse,
    tags=["Desenvolvimento"],
    summary="Verificar a saúde da API e do MySQL",
    operation_id="check_health",
    description="Executa uma consulta SQL de verificação. Não retorna registros do domínio.",
    responses={status: ERROR_RESPONSES[status] for status in (405, 413, 500, 503)},
)


# Modelo para novas rotas protegidas: declare Security na assinatura do endpoint.
# Acrescente os escopos necessários; para dados clínicos, valide também acesso ao registro.
@router.get(
    "/api/v1/me",
    response_model=IdentityResponse,
    tags=["Autenticação"],
    summary="Consultar a identidade autenticada",
    operation_id="get_current_identity",
    description="Valida o JWT e a sessão no MySQL. Exige Bearer e o escopo identity:read.",
    responses={
        status: ERROR_RESPONSES[status]
        for status in (401, 403, 405, 413, 429, 500, 503)
    },
)
def identity(
    user: Annotated[
        AuthenticatedUser, Security(authenticate_request, scopes=["identity:read"])
    ],
):
    return IdentityResponse(subject=user.subject)


@router.get(
    "/api/v1/auth/session",
    response_model=SessionResponse,
    tags=["Autenticação"],
    summary="Consultar a validade do acesso e a necessidade de renovação",
    operation_id="get_session_status",
    description=(
        "Valida o access token antes de executar a consulta. Exige o escopo identity:read. "
        "refresh_required indica proximidade da expiração; use POST /api/v1/auth/refresh. "
        "Sessões encerradas e usuários desativados são recusados imediatamente."
    ),
    responses={
        status: ERROR_RESPONSES[status]
        for status in (401, 403, 405, 413, 429, 500, 503)
    },
)
def validate_session(
    user: Annotated[
        AuthenticatedUser, Security(authenticate_request, scopes=["identity:read"])
    ],
):
    return session_status(user)


@router.get(
    "/api/v1/admin/me",
    response_model=AdministratorResponse,
    tags=["Autenticação"],
    summary="Confirmar acesso administrativo",
    operation_id="get_admin_identity",
    description=(
        "Exige identity:read e admin:access, usuário ativo e perfil ADMINISTRADOR "
        "com USUARIO_GERENCIAR no banco do ProntuarioEdu. Não concede acesso a prontuários."
    ),
    responses={
        status: ERROR_RESPONSES[status]
        for status in (401, 403, 405, 413, 429, 500, 503)
    },
)
def admin_identity(
    admin: Annotated[AdministratorResponse, Depends(require_system_admin)],
):
    return admin


@router.post(
    "/api/v1/auth/refresh",
    response_model=TokenResponse,
    tags=["Autenticação"],
    responses=AUTH_ERRORS,
    summary="Renovar o acesso e rotacionar o refresh token",
    operation_id="refresh_access",
    description=(
        "Recebe refresh_token e scope opcional no JSON. Rotaciona o refresh token, tornando o anterior inválido, "
        "sem prolongar o prazo máximo da sessão. O scope padrão é identity:read; admin:access exige concessão ativa."
    ),
)
def refresh(payload: RefreshRequest):
    return refresh_access(payload)


@router.post(
    "/api/v1/auth/logout",
    status_code=204,
    tags=["Autenticação"],
    responses=AUTH_ERRORS,
    summary="Encerrar a sessão",
    operation_id="logout",
    description=(
        "Revoga a sessão do Bearer validado e bloqueia seus access/refresh tokens. "
        "Exige identity:read e retorna 204 sem corpo. Execute antes de limpar a autorização no Swagger."
    ),
)
def end_session(
    user: Annotated[
        AuthenticatedUser, Security(authenticate_request, scopes=["identity:read"])
    ],
):
    logout(user)
    return Response(status_code=204)


@router.post(
    "/api/v1/auth/password",
    status_code=204,
    tags=["Autenticação"],
    responses=AUTH_ERRORS,
    summary="Trocar senha e encerrar todas as sessões",
    operation_id="change_password",
    description=(
        "Exige Bearer com identity:read e JSON com current_password e new_password (12 a 128 caracteres). "
        "Confere a senha atual, troca seu hash e revoga todas as sessões do usuário. Retorna 204 sem corpo; entre novamente."
    ),
)
def change_password(
    payload: PasswordChangeRequest,
    user: Annotated[
        AuthenticatedUser, Security(authenticate_request, scopes=["identity:read"])
    ],
):
    update_password(user, payload)
    return Response(status_code=204)
