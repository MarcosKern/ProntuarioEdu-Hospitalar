from typing import Annotated

from fastapi import APIRouter, Depends, Security

from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.controllers.admin import require_system_admin
from prontuario_backend.controllers.auth import session_status
from prontuario_backend.controllers.health import health
from prontuario_backend.views.auth import (
    AdministratorResponse,
    IdentityResponse,
    SessionResponse,
)
from prontuario_backend.views.errors import ERROR_RESPONSES
from prontuario_backend.views.health import HealthResponse

router = APIRouter()
router.add_api_route("/health", health, methods=["GET"], response_model=HealthResponse, tags=["Desenvolvimento"],
                     summary="Verificar a saúde da API e do MySQL", operation_id="check_health",
                     description="Executa uma consulta SQL de verificação. Não retorna registros do domínio.",
                     responses={status: ERROR_RESPONSES[status] for status in (405, 413, 500, 503)})


@router.get("/api/v1/me", response_model=IdentityResponse, tags=["Autenticação"],
            summary="Consultar a identidade autenticada", operation_id="get_current_identity",
            description="Valida o access token OIDC e retorna seu subject. Exige Bearer e o escopo identity:read.",
            responses={status: ERROR_RESPONSES[status] for status in (401, 403, 405, 413, 429, 500, 503)})
def identity(user: Annotated[AuthenticatedUser, Security(authenticate_request, scopes=["identity:read"])]):
    return IdentityResponse(subject=user.subject)


@router.get("/api/v1/auth/session", response_model=SessionResponse, tags=["Autenticação"],
            summary="Consultar a validade do acesso e a necessidade de renovação", operation_id="get_session_status",
            description=("Valida o access token antes de executar a consulta. Exige o escopo identity:read. "
                         "refresh_required indica proximidade da expiração; a renovação é feita no provedor OAuth2. "
                         "Esta consulta não verifica logout ou revogação no provedor."),
            responses={status: ERROR_RESPONSES[status] for status in (401, 403, 405, 413, 429, 500, 503)})
def validate_session(user: Annotated[AuthenticatedUser, Security(authenticate_request, scopes=["identity:read"])]):
    return session_status(user)


@router.get("/api/v1/admin/me", response_model=AdministratorResponse, tags=["Autenticação"],
            summary="Confirmar acesso administrativo", operation_id="get_admin_identity",
            description=("Exige identity:read e admin:access, usuário ativo e perfil ADMINISTRADOR "
                         "com USUARIO_GERENCIAR no banco do ProntuarioEdu. Não concede acesso a prontuários."),
            responses={status: ERROR_RESPONSES[status] for status in (401, 403, 405, 413, 429, 500, 503)})
def admin_identity(admin: Annotated[AdministratorResponse, Depends(require_system_admin)]):
    return admin
