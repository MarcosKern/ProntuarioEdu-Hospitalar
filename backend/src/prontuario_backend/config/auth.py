from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from prontuario_backend.config.settings import get_settings

# URLs de exemplo não realizam login. Configure o provedor antes de usar Authorize.
oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl=get_settings().oidc_authorization_url or "https://identity.example.invalid/authorize",
    tokenUrl=get_settings().oidc_token_url or "https://identity.example.invalid/token",
    auto_error=False,
)


@lru_cache(maxsize=4)
def jwks_client(url):
    return jwt.PyJWKClient(url, timeout=5)


def current_user(token: str | None = Depends(oauth2)):
    if not token:
        raise HTTPException(401, "Token necessário", headers={"WWW-Authenticate": "Bearer"})
    issuer = get_settings().oidc_issuer
    audience = get_settings().oidc_audience
    jwks = get_settings().oidc_jwks_url
    if not all((issuer, audience, jwks)):
        raise HTTPException(503, "Provedor de autenticação não configurado")
    if not issuer.startswith("https://") or not jwks.startswith("https://"):
        raise HTTPException(503, "O provedor deve usar HTTPS")
    try:
        key = jwks_client(jwks).get_signing_key_from_jwt(token)
        return jwt.decode(
            token, key.key, algorithms=["RS256"], audience=audience,
            issuer=issuer, options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(503, "Provedor de autenticação indisponível") from None
    except jwt.PyJWTError:
        raise HTTPException(401, "Token inválido", headers={"WWW-Authenticate": "Bearer"}) from None
