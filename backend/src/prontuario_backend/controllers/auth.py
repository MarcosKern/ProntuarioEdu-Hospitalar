"""Fluxo de login, renovação e encerramento de sessões da aplicação."""
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs
from uuid import UUID, uuid4

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from prontuario_backend.config.auth import (
    AuthenticatedUser,
    hash_password,
    issue_access_token,
    signing_secret,
    verify_password,
)
from prontuario_backend.config.database import engine
from prontuario_backend.config.settings import get_settings
from prontuario_backend.models import users
from prontuario_backend.views.auth import LoginRequest, SessionResponse, TokenResponse

# Hash de comparação para logins inexistentes; nenhuma senha real e nenhum I/O na importação.
DUMMY_HASH = "scrypt$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def allowed_scopes(connection, subject, requested):
    available = {"identity:read"}
    if users.system_admin(connection, subject):
        available.add("admin:access")
    scopes = frozenset(requested.split()) if requested else frozenset({"identity:read"})
    if not scopes.issubset(available):
        raise HTTPException(400, "Escopo não permitido")
    return scopes


def token_response(subject, session_id, scopes, refresh):
    access, expires = issue_access_token(subject, session_id, scopes)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=expires, scope=" ".join(sorted(scopes)))


def login(username, password, requested):
    signing_secret()  # Falhar antes de qualquer mutação se o emissor não estiver configurado.
    response = None
    try:
        with engine().begin() as connection:
            account = users.account_for_login(connection, username)
            valid = verify_password(password, account["hash_senha"] if account and account["hash_senha"] else DUMMY_HASH)
            if account and account["provedor"] == "local" and account["ativo"] and not account["bloqueado"] and valid:
                scopes = allowed_scopes(connection, account["id"], requested)
                session_id = str(uuid4())
                refresh = session_id + "." + secrets.token_urlsafe(48)
                expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=get_settings().auth_refresh_token_days)
                users.create_login_session(connection, account["id"], hashlib.sha256(refresh.encode()).hexdigest(), expires, session_id)
                response = token_response(account["id"], session_id, scopes, refresh)
            elif account and account["ativo"] and account["provedor"] == "local" and not account["bloqueado"]:
                users.login_failure(connection, account["id"])
    except SQLAlchemyError:
        raise HTTPException(503, "Autenticação indisponível") from None
    if response is None:
        raise HTTPException(401, "Usuário ou senha inválidos", headers={"WWW-Authenticate": "Bearer"})
    return response


async def token_endpoint(request: Request):
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/x-www-form-urlencoded":
        raise HTTPException(415, "Envie formulário application/x-www-form-urlencoded")
    try:
        form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True, max_num_fields=10, errors="strict")
    except (ValueError, UnicodeError):
        raise HTTPException(400, "Formulário de login inválido") from None
    if any(len(values) != 1 for values in form.values()):
        raise HTTPException(400, "Campos repetidos no formulário de login")
    try:
        payload = LoginRequest.model_validate({key: values[0] for key, values in form.items()})
    except ValidationError:
        raise HTTPException(400, "Formulário de login inválido") from None
    return await run_in_threadpool(login, payload.username, payload.password.get_secret_value(), payload.scope)


def refresh_access(payload):
    signing_secret()
    refresh = payload.refresh_token.get_secret_value()
    try:
        session_id, secret = refresh.split(".", 1)
        if str(UUID(session_id)) != session_id or len(secret) != 64:
            raise ValueError("Invalid refresh token")
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(401, "Refresh token inválido") from None
    try:
        with engine().begin() as connection:
            session = users.active_session(connection, session_id, lock=True)
            if not session or not hmac.compare_digest(session["refresh_token_hash"], hashlib.sha256(refresh.encode()).hexdigest()):
                raise HTTPException(401, "Refresh token inválido ou expirado")
            scopes = allowed_scopes(connection, session["usuario_id"], payload.scope)
            rotated = session_id + "." + secrets.token_urlsafe(48)
            users.rotate_refresh(connection, session_id, hashlib.sha256(rotated.encode()).hexdigest())
            return token_response(session["usuario_id"], session_id, scopes, rotated)
    except SQLAlchemyError:
        raise HTTPException(503, "Autenticação indisponível") from None


def logout(user):
    try:
        with engine().begin() as connection:
            users.revoke_session(connection, user.session_id, user.subject)
    except SQLAlchemyError:
        raise HTTPException(503, "Autenticação indisponível") from None


def update_password(user, payload):
    try:
        with engine().begin() as connection:
            current = users.account_password(connection, user.subject)
            if not verify_password(payload.current_password.get_secret_value(), current):
                raise HTTPException(401, "Senha atual inválida")
            if payload.new_password.get_secret_value() == payload.current_password.get_secret_value():
                raise HTTPException(400, "Escolha uma senha diferente da atual")
            users.change_password(connection, user.subject, hash_password(payload.new_password.get_secret_value()))
    except SQLAlchemyError:
        raise HTTPException(503, "Autenticação indisponível") from None


def session_status(user: AuthenticatedUser) -> SessionResponse:
    remaining = max(0, int((user.expires_at - datetime.now(UTC)).total_seconds()))
    return SessionResponse(subject=user.subject, expires_at=user.expires_at, expires_in_seconds=remaining,
                           refresh_required=remaining <= get_settings().auth_refresh_window_seconds)
