from fastapi import HTTPException

from prontuario_backend.models import medicamentos


def criar(dados):
    return medicamentos.criar(dados)


def listar(limite, deslocamento, nome):
    items, total = medicamentos.listar_ativos_paginados(limite, deslocamento, nome)
    return {
        "items": items,
        "total": total,
        "limit": limite,
        "offset": deslocamento,
    }


def buscar(medicamento_id):
    medicamento = medicamentos.buscar_por_id(medicamento_id)
    if medicamento is None:
        raise HTTPException(404, "Medicamento não encontrado")
    return medicamento


def atualizar(medicamento_id, dados):
    medicamento = medicamentos.atualizar(medicamento_id, dados)
    if medicamento is None:
        raise HTTPException(404, "Medicamento não encontrado")
    return medicamento


def desativar(medicamento_id):
    if medicamentos.desativar(medicamento_id) is None:
        raise HTTPException(404, "Medicamento não encontrado")
