from uuid import UUID

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    request_id: UUID
    message: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


def error_body(code: str, request_id: str, message: str | None = None):
    """Mantém o mesmo envelope público nos handlers e no middleware."""
    return ErrorResponse(
        error=ErrorDetail(code=code, request_id=request_id, message=message)
    ).model_dump(mode="json", exclude_none=True)


ERROR_RESPONSES = {
    status: {"model": ErrorResponse, "description": description}
    for status, description in {
        400: "Requisição inválida",
        401: "Credencial ausente ou inválida",
        403: "Acesso negado",
        404: "Recurso não encontrado",
        405: "Método não permitido",
        413: "Corpo acima do limite",
        415: "Tipo de conteúdo não suportado",
        422: "Entrada inválida",
        429: "Limite de requisições excedido",
        500: "Erro interno",
        503: "Dependência indisponível ou não configurada",
    }.items()
}

ERROR_RESPONSES[401]["headers"] = {
    "WWW-Authenticate": {"schema": {"type": "string"}, "description": "Bearer"}
}
ERROR_RESPONSES[429]["headers"] = {
    "Retry-After": {
        "schema": {"type": "integer"},
        "description": "Segundos até nova tentativa",
    }
}
