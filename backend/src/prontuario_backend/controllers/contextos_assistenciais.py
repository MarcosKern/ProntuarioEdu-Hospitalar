from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from prontuario_backend.models import contextos_assistenciais


def criar(dados):
    try:
        return contextos_assistenciais.criar(dados)
    except IntegrityError as exc:
        if _duplicidade_de_codigo(exc):
            raise HTTPException(
                409, "Código de contexto assistencial já cadastrado"
            ) from None
        raise


def listar(limite, deslocamento):
    items, total = contextos_assistenciais.listar_ativos_paginados(
        limite, deslocamento
    )
    return {
        "items": items,
        "total": total,
        "limit": limite,
        "offset": deslocamento,
    }


def buscar(contexto_id):
    contexto = contextos_assistenciais.buscar_por_id(contexto_id)
    if contexto is None:
        raise HTTPException(404, "Contexto assistencial não encontrado")
    return contexto


def atualizar(contexto_id, dados):
    contexto = contextos_assistenciais.atualizar(contexto_id, dados)
    if contexto is None:
        raise HTTPException(404, "Contexto assistencial não encontrado")
    return contexto


def desativar(contexto_id):
    if contextos_assistenciais.desativar(contexto_id) is None:
        raise HTTPException(404, "Contexto assistencial não encontrado")


def _duplicidade_de_codigo(exc):
    args = getattr(exc.orig, "args", ())
    if len(args) < 2 or args[0] != 1062 or not isinstance(args[1], str):
        return False
    key = args[1].rsplit(" for key ", 1)[-1].strip("'`")
    return key in {
        "codigo",
        "assistencial__contextos_assistenciais.codigo",
    }
