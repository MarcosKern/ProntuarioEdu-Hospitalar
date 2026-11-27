from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from prontuario_backend.controllers import unidades
from prontuario_backend.views.errors import ERROR_RESPONSES, ErrorResponse
from prontuario_backend.views.pagination import PageResponse, PaginationParams
from prontuario_backend.views.unidades import (
    UnidadeCreate,
    UnidadePatch,
    UnidadeResponse,
)

router = APIRouter()
ERRORS = (405, 413, 415, 422, 500, 503)
READ_ERRORS = (405, 413, 422, 500, 503)
NOT_FOUND_ERRORS = (404, *READ_ERRORS)
CREATE_RESPONSES = {
    **{status: ERROR_RESPONSES[status] for status in ERRORS},
    409: {
        "model": ErrorResponse,
        "description": "Código de unidade já cadastrado",
    },
}


@router.post(
    "/api/v1/unidades",
    response_model=UnidadeResponse,
    status_code=201,
    tags=["Unidades"],
    summary="Cadastrar unidade",
    description="Cria uma unidade com código único. A unidade começa ativa.",
    operation_id="criar_unidade",
    responses=CREATE_RESPONSES,
)
def criar_unidade(payload: UnidadeCreate):
    return unidades.criar(payload.model_dump())


@router.get(
    "/api/v1/unidades",
    response_model=PageResponse[UnidadeResponse],
    tags=["Unidades"],
    summary="Listar unidades ativas",
    description="Retorna unidades ativas ordenadas por nome e ID, em páginas.",
    operation_id="listar_unidades",
    responses={status: ERROR_RESPONSES[status] for status in READ_ERRORS},
)
def listar_unidades(params: Annotated[PaginationParams, Query()]):
    return unidades.listar(params.limit, params.offset)


@router.get(
    "/api/v1/unidades/{id}",
    response_model=UnidadeResponse,
    tags=["Unidades"],
    summary="Consultar unidade",
    description="Consulta uma unidade pelo UUID.",
    operation_id="buscar_unidade",
    responses={status: ERROR_RESPONSES[status] for status in NOT_FOUND_ERRORS},
)
def buscar_unidade(id: UUID):
    return unidades.buscar(str(id))


@router.patch(
    "/api/v1/unidades/{id}",
    response_model=UnidadeResponse,
    tags=["Unidades"],
    summary="Atualizar unidade",
    description="Atualiza parcialmente o nome e/ou o tipo. Código e ID são preservados.",
    operation_id="atualizar_unidade",
    responses={
        **{status: ERROR_RESPONSES[status] for status in ERRORS},
        404: ERROR_RESPONSES[404],
    },
)
def atualizar_unidade(id: UUID, payload: UnidadePatch):
    return unidades.atualizar(str(id), payload.model_dump(exclude_unset=True))


@router.delete(
    "/api/v1/unidades/{id}",
    status_code=204,
    tags=["Unidades"],
    summary="Desativar unidade",
    description="Desativa a unidade sem excluir o registro do banco.",
    operation_id="desativar_unidade",
    responses={
        status: ERROR_RESPONSES[status] for status in NOT_FOUND_ERRORS
    },
)
def desativar_unidade(id: UUID):
    unidades.desativar(str(id))
    return Response(status_code=204)
