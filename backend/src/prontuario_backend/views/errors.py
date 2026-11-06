from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    request_id: str
    message: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


ERROR_RESPONSES = {
    status: {"model": ErrorResponse, "description": description}
    for status, description in {
        400: "Requisição inválida", 401: "Credencial ausente ou inválida", 403: "Acesso negado",
        404: "Recurso não encontrado", 405: "Método não permitido", 413: "Corpo acima do limite",
        422: "Entrada inválida", 429: "Limite de requisições excedido", 500: "Erro interno",
        503: "Dependência indisponível ou não configurada",
    }.items()
}

ERROR_RESPONSES[401]["headers"] = {"WWW-Authenticate": {"schema": {"type": "string"}, "description": "Bearer"}}
ERROR_RESPONSES[429]["headers"] = {"Retry-After": {"schema": {"type": "integer"}, "description": "Segundos até nova tentativa"}}
