from fastapi import HTTPException
from prontuario_backend.models.health import database_ready
from prontuario_backend.views.health import health_response
from sqlalchemy.exc import SQLAlchemyError


def health():
    try:
        ready = database_ready()
    except SQLAlchemyError:
        raise HTTPException(503, "Banco indisponível") from None
    if not ready:
        raise HTTPException(503, "Banco indisponível")
    return health_response()
