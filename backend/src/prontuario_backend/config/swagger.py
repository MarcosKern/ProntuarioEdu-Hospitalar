"""Swagger/OpenAPI configuration shared by local and Codespaces development."""

from fastapi import FastAPI

from prontuario_backend.config.auth import API_SCOPES, oauth2
from prontuario_backend.config.settings import Settings


def swagger_config(settings: Settings):
    production = settings.app_env == "production"
    oauth = {
        "appName": "ProntuarioEdu — Swagger",
        "usePkceWithAuthorizationCodeGrant": True,
        "useBasicAuthenticationWithAccessCodeGrant": False,
        "scopeSeparator": " ",
        "scopes": list(API_SCOPES),
    }
    if settings.swagger_client_id:
        oauth["clientId"] = settings.swagger_client_id
    return {
        "title": "ProntuarioEdu",
        "version": "0.2.0",
        "description": (
            "API compartilhada pelos aplicativos Desktop, Web e futuras integrações. "
            "A documentação apresenta somente as rotas implementadas. "
            "O login usa um provedor OAuth2/OIDC externo; não há contas padrão."
        ),
        "docs_url": None if production else "/docs",
        "redoc_url": None,
        "openapi_url": None if production else "/openapi.json",
        "swagger_ui_oauth2_redirect_url": None if production else "/docs/oauth2-redirect",
        # Keep requests on the browser's origin, including private Codespaces HTTPS URLs.
        "servers": [{"url": "/", "description": "Mesma origem usada para acessar a API"}],
        "openapi_tags": [
            {"name": "Desenvolvimento", "description": "Verificação da API e da conexão MySQL."},
            {"name": "Autenticação", "description": "Identidade validada pelo provedor OAuth2/OIDC."},
        ],
        "swagger_ui_parameters": {
            "persistAuthorization": False,
            "displayRequestDuration": True,
            "filter": True,
        },
        "swagger_ui_init_oauth": oauth,
    }


def configure_swagger_auth(app: FastAPI, settings: Settings):
    """Liga o botão Authorize ao provedor configurado nesta instância da API."""
    default_openapi = app.openapi
    defaults = oauth2.model.flows.authorizationCode

    def configured_openapi():
        schema = default_openapi()
        flow = schema["components"]["securitySchemes"][oauth2.scheme_name]["flows"]["authorizationCode"]
        flow["authorizationUrl"] = settings.oidc_authorization_url or defaults.authorizationUrl
        flow["tokenUrl"] = settings.oidc_token_url or defaults.tokenUrl
        if settings.oidc_token_url:
            flow["refreshUrl"] = settings.oidc_token_url
        return schema

    app.openapi = configured_openapi
