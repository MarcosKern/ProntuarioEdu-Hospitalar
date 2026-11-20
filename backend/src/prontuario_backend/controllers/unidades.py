from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from prontuario_backend.models import unidades


def criar(dados):
    try:
        return unidades.criar(dados)
    except IntegrityError as exc:
        if _duplicidade_de_codigo(exc):
            raise HTTPException(409, "Código de unidade já cadastrado") from None
        raise


def listar(limite, deslocamento):
    items, total = unidades.listar_ativas_paginadas(limite, deslocamento)
    return {
        "items": items,
        "total": total,
        "limit": limite,
        "offset": deslocamento,
    }


def buscar(unidade_id):
    unidade = unidades.buscar_por_id(unidade_id)
    if unidade is None:
        raise HTTPException(404, "Unidade não encontrada")
    return unidade


def atualizar(unidade_id, dados):
    unidade = unidades.atualizar(unidade_id, dados)
    if unidade is None:
        raise HTTPException(404, "Unidade não encontrada")
    return unidade


def desativar(unidade_id):
    if unidades.desativar(unidade_id) is None:
        raise HTTPException(404, "Unidade não encontrada")


def _duplicidade_de_codigo(exc):
    args = getattr(exc.orig, "args", ())
    if len(args) < 2 or args[0] != 1062 or not isinstance(args[1], str):
        return False
    key = args[1].rsplit(" for key ", 1)[-1].strip("'`")
    return key in {"codigo", "cadastro__unidades.codigo"}
