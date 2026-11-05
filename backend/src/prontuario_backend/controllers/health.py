from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from prontuario_backend.models.health import database_ready
from prontuario_backend.views.health import health_response


def health():
    try:
        ready = database_ready()
    except SQLAlchemyError:
        raise HTTPException(503, "Banco indisponível") from None
    if not ready:
        raise HTTPException(503, "Banco indisponível")
    return health_response()
