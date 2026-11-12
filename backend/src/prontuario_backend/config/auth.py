import math
import re
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from json import JSONDecodeError
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes

from prontuario_backend.config.settings import get_settings

API_SCOPES = {
    "identity:read": "Consultar a própria identidade e a validade do acesso",
    "admin:access": "Consultar a própria identidade administrativa; não concede acesso a prontuários",
}
SCOPE_TOKEN = re.compile(r'[\x21\x23-\x5b\x5d-\x7e]+')

# O Swagger preenche as URLs reais por instância em configure_swagger_auth.
# Os valores abaixo só aparecem enquanto o provedor não estiver configurado.
oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://identity.example.invalid/authorize",
    tokenUrl="https://identity.example.invalid/token",
    scopes=API_SCOPES,
    description=("Use Authorize para entrar no provedor OAuth2/OIDC e obter um access token por "
                 "Authorization Code com PKCE. O cliente público não usa client secret. "
                 "Configure as URLs OIDC e SWAGGER_CLIENT_ID no ambiente."),
    auto_error=False,
)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identidade obtida exclusivamente de um access token verificado."""

    subject: str
    expires_at: datetime
    scopes: frozenset[str]


@lru_cache(maxsize=4)
def jwks_client(url):
    context = ssl.create_default_context(cafile=get_settings().oidc_ssl_ca or None)
    return jwt.PyJWKClient(url, timeout=5, ssl_context=context)


def invalid_token(message="Token inválido"):
    return HTTPException(401, message, headers={"WWW-Authenticate": 'Bearer error="invalid_token"'})


def validate_access_token(token: str) -> AuthenticatedUser:
    """Verifica assinatura e claims; nunca emite ou renova tokens."""
    settings = get_settings()
    issuer = settings.oidc_issuer
    audience = settings.oidc_audience
    jwks = settings.oidc_jwks_url
    if not all((issuer, audience, jwks)):
        raise HTTPException(503, "Provedor de autenticação não configurado")
    if not issuer.startswith("https://") or not jwks.startswith("https://"):
        raise HTTPException(503, "O provedor deve usar HTTPS")

    # O header ainda não é confiável: serve apenas para recusar formatos indevidos.
    # A URL JWKS vem da configuração; headers jku/x5u não escolhem destinos de rede.
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str) or not header["kid"]:
            raise jwt.InvalidTokenError("Unsupported signing header")
    except jwt.PyJWTError:
        raise invalid_token() from None

    try:
        key = jwks_client(jwks).get_signing_key_from_jwt(token)
    except (jwt.PyJWKClientConnectionError, jwt.PyJWKSetError, JSONDecodeError):
        raise HTTPException(503, "Provedor de autenticação indisponível") from None
    except jwt.PyJWTError:
        raise invalid_token() from None

    try:
        claims = jwt.decode(
            token, key.key, algorithms=["RS256"], audience=audience,
            issuer=issuer, options={"require": ["exp", "iss", "aud", "sub"]},
        )
        for name in ("exp", "iat", "nbf"):
            if name in claims and (type(claims[name]) not in (int, float) or not math.isfinite(claims[name])):
                raise jwt.InvalidTokenError("Invalid NumericDate")
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject or len(subject) > 255:
            raise jwt.InvalidTokenError("Invalid subject")
        scope = claims.get(settings.oidc_scope_claim, "")
        if not isinstance(scope, str):
            raise jwt.InvalidTokenError("Invalid scope claim")
        scopes = frozenset(scope.split(" ")) - {""}
        if any(not SCOPE_TOKEN.fullmatch(value) for value in scopes):
            raise jwt.InvalidTokenError("Invalid scope value")
        return AuthenticatedUser(subject, datetime.fromtimestamp(claims["exp"], UTC), scopes)
    except jwt.ExpiredSignatureError:
        raise invalid_token("Token expirado; renove o acesso no provedor de autenticação") from None
    except (jwt.PyJWTError, ValueError, TypeError, OverflowError, OSError):
        raise invalid_token() from None


def authenticate_request(
    security_scopes: SecurityScopes,
    token: Annotated[str | None, Depends(oauth2)],
) -> AuthenticatedUser:
    """Dependência executada antes do endpoint: autentica e exige seus escopos."""
    if not token:
        raise HTTPException(401, "Token necessário", headers={"WWW-Authenticate": "Bearer"})
    user = validate_access_token(token)
    if not set(security_scopes.scopes).issubset(user.scopes):
        challenge = f'Bearer error="insufficient_scope", scope="{security_scopes.scope_str}"'
        raise HTTPException(403, "Escopo insuficiente", headers={"WWW-Authenticate": challenge})
    return user
