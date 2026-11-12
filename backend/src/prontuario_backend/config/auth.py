"""Hash de senhas, emissão JWT e autenticação antes dos endpoints."""
import base64
import math
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

import jwt
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.exc import SQLAlchemyError

from prontuario_backend.config.database import engine
from prontuario_backend.config.settings import get_settings
from prontuario_backend.models.users import active_session, system_admin

API_SCOPES = {
    "identity:read": "Consultar a própria identidade e a validade do acesso",
    "admin:access": "Administrar usuários; não concede acesso a prontuários",
}
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", scopes=API_SCOPES, auto_error=False,
                             description="Entre com usuário e senha da aplicação. O Swagger envia o JWT como Bearer.")


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    expires_at: datetime
    scopes: frozenset[str]
    session_id: str = ""


def hash_password(value: str) -> str:
    if not 12 <= len(value) <= 128:
        raise ValueError("A senha deve ter entre 12 e 128 caracteres")
    salt = secrets.token_bytes(16)
    digest = Scrypt(salt=salt, length=32, n=2**15, r=8, p=3).derive(value.encode())
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(value: str, encoded: str) -> bool:
    try:
        algorithm, salt, digest = encoded.split("$")
        if algorithm != "scrypt" or not 1 <= len(value) <= 128:
            return False
        salt, digest = base64.b64decode(salt, validate=True), base64.b64decode(digest, validate=True)
        if len(salt) != 16 or len(digest) != 32:
            return False
        Scrypt(salt=salt, length=32, n=2**15, r=8, p=3).verify(value.encode(), digest)
        return True
    except (ValueError, TypeError, AttributeError, InvalidKey):
        return False


def signing_secret():
    secret = get_settings().auth_jwt_secret
    if not secret:
        raise HTTPException(503, "Configure AUTH_JWT_SECRET para habilitar o login")
    return secret.get_secret_value()


def issue_access_token(subject: str, session_id: str, scopes: frozenset[str]):
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.auth_access_token_minutes)
    claims = {"iss": settings.auth_jwt_issuer, "aud": settings.auth_jwt_audience,
              "sub": subject, "sid": session_id, "jti": str(uuid4()), "iat": now, "exp": expires,
              "token_use": "access", "scope": " ".join(sorted(scopes))}
    return jwt.encode(claims, signing_secret(), algorithm="HS256"), settings.auth_access_token_minutes * 60


def invalid_token(message="Token inválido"):
    return HTTPException(401, message, headers={"WWW-Authenticate": 'Bearer error="invalid_token"'})


def validate_access_token(token: str) -> AuthenticatedUser:
    settings = get_settings()
    secret = signing_secret()
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"], audience=settings.auth_jwt_audience,
                            issuer=settings.auth_jwt_issuer,
                            options={"require": ["exp", "iat", "iss", "aud", "sub", "sid", "jti", "token_use", "scope"]})
        for name in ("exp", "iat", "nbf"):
            if name in claims and (type(claims[name]) not in (int, float) or not math.isfinite(claims[name])):
                raise jwt.InvalidTokenError("Invalid NumericDate")
        subject, session_id = claims["sub"], claims["sid"]
        if str(UUID(subject)) != subject or str(UUID(session_id)) != session_id or claims["token_use"] != "access":
            raise jwt.InvalidTokenError("Invalid identity")
        if not isinstance(claims["scope"], str):
            raise jwt.InvalidTokenError("Invalid scopes")
        scopes = frozenset(claims["scope"].split(" ")) - {""}
        if not scopes.issubset(API_SCOPES):
            raise jwt.InvalidTokenError("Invalid scopes")
        expires = datetime.fromtimestamp(claims["exp"], UTC)
    except jwt.ExpiredSignatureError:
        raise invalid_token("Token expirado; renove o acesso") from None
    except (jwt.PyJWTError, ValueError, TypeError, AttributeError, OverflowError, OSError):
        raise invalid_token() from None
    try:
        with engine().connect() as connection:
            if not active_session(connection, session_id, subject):
                raise invalid_token("Sessão encerrada ou usuário indisponível")
            # Reavaliar a concessão administrativa em cada requisição.
            if "admin:access" in scopes and not system_admin(connection, subject):
                scopes = scopes - {"admin:access"}
    except SQLAlchemyError:
        raise HTTPException(503, "Autenticação indisponível") from None
    return AuthenticatedUser(subject, expires, scopes, session_id)


def authenticate_request(security_scopes: SecurityScopes, token: Annotated[str | None, Depends(oauth2)]) -> AuthenticatedUser:
    if not token:
        raise HTTPException(401, "Token necessário", headers={"WWW-Authenticate": "Bearer"})
    user = validate_access_token(token)
    if not set(security_scopes.scopes).issubset(user.scopes):
        raise HTTPException(403, "Escopo insuficiente", headers={"WWW-Authenticate":
                            f'Bearer error="insufficient_scope", scope="{security_scopes.scope_str}"'})
    return user
