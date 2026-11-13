from typing import Annotated

from fastapi import HTTPException, Security
from sqlalchemy.exc import SQLAlchemyError

from prontuario_backend.config.auth import AuthenticatedUser, authenticate_request
from prontuario_backend.config.database import engine
from prontuario_backend.models.users import system_admin
from prontuario_backend.views.auth import AdministratorResponse


def require_system_admin(
    user: Annotated[
        AuthenticatedUser,
        Security(authenticate_request, scopes=["identity:read", "admin:access"]),
    ],
) -> AdministratorResponse:
    """Confere o usuário e a concessão ativa no banco da aplicação antes da operação."""
    try:
        with engine().connect() as connection:
            account = system_admin(connection, user.subject)
    except SQLAlchemyError:
        raise HTTPException(503, "Cadastro de usuários indisponível") from None
    if not account:
        raise HTTPException(403, "Usuário sem permissão administrativa ativa")
    return AdministratorResponse(
        subject=user.subject,
        user_id=account["id"],
        login=account["login"],
        name=account["nome"],
    )
