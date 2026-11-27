from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from prontuario_backend.controllers import medicamentos
from prontuario_backend.views.errors import ERROR_RESPONSES
from prontuario_backend.views.medicamentos import (
    MedicamentoCreate,
    MedicamentoListQuery,
    MedicamentoPatch,
    MedicamentoResponse,
)
from prontuario_backend.views.pagination import PageResponse

router = APIRouter()
ERRORS = (405, 413, 415, 422, 500, 503)
READ_ERRORS = (405, 413, 422, 500, 503)
NOT_FOUND_ERRORS = (404, *READ_ERRORS)


@router.post(
    "/api/v1/medicamentos",
    response_model=MedicamentoResponse,
    status_code=201,
    tags=["Medicamentos"],
    summary="Cadastrar medicamento",
    description="Adiciona um medicamento ao catálogo.",
    operation_id="criar_medicamento",
    responses={status: ERROR_RESPONSES[status] for status in ERRORS},
)
def criar_medicamento(payload: MedicamentoCreate):
    return medicamentos.criar(payload.model_dump())


@router.get(
    "/api/v1/medicamentos",
    response_model=PageResponse[MedicamentoResponse],
    tags=["Medicamentos"],
    summary="Listar medicamentos ativos",
    description=(
        "Lista o catálogo ativo por nome, com paginação e filtro opcional literal."
    ),
    operation_id="listar_medicamentos",
    responses={status: ERROR_RESPONSES[status] for status in READ_ERRORS},
)
def listar_medicamentos(params: Annotated[MedicamentoListQuery, Query()]):
    return medicamentos.listar(params.limit, params.offset, params.nome)


@router.get(
    "/api/v1/medicamentos/{id}",
    response_model=MedicamentoResponse,
    tags=["Medicamentos"],
    summary="Consultar medicamento",
    description="Consulta um medicamento pelo UUID.",
    operation_id="buscar_medicamento",
    responses={status: ERROR_RESPONSES[status] for status in NOT_FOUND_ERRORS},
)
def buscar_medicamento(id: UUID):
    return medicamentos.buscar(str(id))


@router.patch(
    "/api/v1/medicamentos/{id}",
    response_model=MedicamentoResponse,
    tags=["Medicamentos"],
    summary="Atualizar medicamento",
    description="Atualiza parcialmente os campos permitidos do catálogo.",
    operation_id="atualizar_medicamento",
    responses={
        **{status: ERROR_RESPONSES[status] for status in ERRORS},
        404: ERROR_RESPONSES[404],
    },
)
def atualizar_medicamento(id: UUID, payload: MedicamentoPatch):
    return medicamentos.atualizar(str(id), payload.model_dump(exclude_unset=True))


@router.delete(
    "/api/v1/medicamentos/{id}",
    status_code=204,
    tags=["Medicamentos"],
    summary="Desativar medicamento",
    description="Desativa o medicamento sem remover o registro do catálogo.",
    operation_id="desativar_medicamento",
    responses={status: ERROR_RESPONSES[status] for status in NOT_FOUND_ERRORS},
)
def desativar_medicamento(id: UUID):
    medicamentos.desativar(str(id))
    return Response(status_code=204)
