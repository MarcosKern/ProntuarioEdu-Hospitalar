from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from prontuario_backend.controllers import contextos_assistenciais
from prontuario_backend.views.contextos_assistenciais import (
    ContextoAssistencialCreate,
    ContextoAssistencialPatch,
    ContextoAssistencialResponse,
)
from prontuario_backend.views.errors import ERROR_RESPONSES, ErrorResponse
from prontuario_backend.views.pagination import PageResponse, PaginationParams

router = APIRouter()
ERRORS = (405, 413, 415, 422, 500, 503)
READ_ERRORS = (405, 413, 422, 500, 503)
NOT_FOUND_ERRORS = (404, *READ_ERRORS)
CREATE_RESPONSES = {
    **{status: ERROR_RESPONSES[status] for status in ERRORS},
    409: {
        "model": ErrorResponse,
        "description": "Código de contexto assistencial já cadastrado",
    },
}


@router.post(
    "/api/v1/contextos-assistenciais",
    response_model=ContextoAssistencialResponse,
    status_code=201,
    tags=["Contextos assistenciais"],
    summary="Cadastrar contexto assistencial",
    description="Cria um contexto assistencial com código único. O contexto começa ativo.",
    operation_id="criar_contexto_assistencial",
    responses=CREATE_RESPONSES,
)
def criar_contexto_assistencial(payload: ContextoAssistencialCreate):
    return contextos_assistenciais.criar(payload.model_dump())


@router.get(
    "/api/v1/contextos-assistenciais",
    response_model=PageResponse[ContextoAssistencialResponse],
    tags=["Contextos assistenciais"],
    summary="Listar contextos assistenciais ativos",
    description="Retorna contextos ativos ordenados por nome e ID, em páginas.",
    operation_id="listar_contextos_assistenciais",
    responses={status: ERROR_RESPONSES[status] for status in READ_ERRORS},
)
def listar_contextos_assistenciais(
    params: Annotated[PaginationParams, Query()],
):
    return contextos_assistenciais.listar(params.limit, params.offset)


@router.get(
    "/api/v1/contextos-assistenciais/{id}",
    response_model=ContextoAssistencialResponse,
    tags=["Contextos assistenciais"],
    summary="Consultar contexto assistencial",
    description="Consulta um contexto assistencial pelo UUID.",
    operation_id="buscar_contexto_assistencial",
    responses={status: ERROR_RESPONSES[status] for status in NOT_FOUND_ERRORS},
)
def buscar_contexto_assistencial(id: UUID):
    return contextos_assistenciais.buscar(str(id))


@router.patch(
    "/api/v1/contextos-assistenciais/{id}",
    response_model=ContextoAssistencialResponse,
    tags=["Contextos assistenciais"],
    summary="Atualizar contexto assistencial",
    description="Atualiza parcialmente nome, tipo e nível de cuidado.",
    operation_id="atualizar_contexto_assistencial",
    responses={
        **{status: ERROR_RESPONSES[status] for status in ERRORS},
        404: ERROR_RESPONSES[404],
    },
)
def atualizar_contexto_assistencial(
    id: UUID,
    payload: ContextoAssistencialPatch,
):
    return contextos_assistenciais.atualizar(
        str(id), payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/api/v1/contextos-assistenciais/{id}",
    status_code=204,
    tags=["Contextos assistenciais"],
    summary="Desativar contexto assistencial",
    description="Desativa o contexto sem excluir o registro do banco.",
    operation_id="desativar_contexto_assistencial",
    responses={
        status: ERROR_RESPONSES[status] for status in NOT_FOUND_ERRORS
    },
)
def desativar_contexto_assistencial(id: UUID):
    contextos_assistenciais.desativar(str(id))
    return Response(status_code=204)
