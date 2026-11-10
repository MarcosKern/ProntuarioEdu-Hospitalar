from fastapi import APIRouter, Depends
from pydantic import BaseModel

from prontuario_backend.config.auth import current_user
from prontuario_backend.controllers.health import health
from prontuario_backend.views.errors import ERROR_RESPONSES
from prontuario_backend.views.health import HealthResponse

router = APIRouter()
router.add_api_route("/health", health, methods=["GET"], response_model=HealthResponse, tags=["Desenvolvimento"],
                     summary="Verificar a saúde da API e do MySQL", operation_id="check_health",
                     description="Executa uma consulta SQL de verificação. Não retorna registros do domínio.",
                     responses={status: ERROR_RESPONSES[status] for status in (405, 413, 500, 503)})


class IdentityResponse(BaseModel):
    subject: str


@router.get("/api/v1/me", response_model=IdentityResponse, tags=["Autenticação"],
            summary="Consultar a identidade autenticada", operation_id="get_current_identity",
            description="Valida o token do provedor OIDC e retorna seu subject. Exige autenticação Bearer.",
            responses={status: ERROR_RESPONSES[status] for status in (401, 405, 413, 429, 500, 503)})
def identity(user=Depends(current_user)):  # noqa: B008 - FastAPI dependency injection
    return IdentityResponse(subject=user["sub"])
