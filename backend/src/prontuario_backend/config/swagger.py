"""Swagger na mesma origem da API, com login local por usuário e senha."""

from prontuario_backend.config.settings import Settings


def swagger_config(settings: Settings):
    production = settings.app_env == "production"
    return {
        "title": "ProntuarioEdu",
        "version": "0.3.0",
        "description": "API MVC para Desktop e Web. Login local, senhas com hash e autenticação JWT.",
        "docs_url": None if production else "/docs",
        "redoc_url": None,
        "openapi_url": None if production else "/openapi.json",
        "swagger_ui_oauth2_redirect_url": None,
        "servers": [
            {"url": "/", "description": "Mesma origem usada para acessar a API"}
        ],
        "openapi_tags": [
            {"name": "Desenvolvimento", "description": "Saúde da API e do MySQL."},
            {
                "name": "Unidades",
                "description": "Cadastro e consulta de unidades.",
            },
            {
                "name": "Autenticação",
                "description": "Login, tokens e sessões da aplicação.",
            },
        ],
        "swagger_ui_parameters": {
            "persistAuthorization": False,
            "displayRequestDuration": True,
            "filter": True,
        },
        "swagger_ui_init_oauth": {
            "appName": "ProntuarioEdu",
            "scopes": ["identity:read"],
        },
    }


def enable_bearer_token_input(app):
    """Documenta o JWT já emitido como alternativa ao formulário de login."""
    original_openapi = app.openapi

    def openapi():
        schema = original_openapi()
        schemes = schema.setdefault("components", {}).setdefault("securitySchemes", {})
        schemes["BearerToken"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Cole apenas o access_token, sem o prefixo Bearer. Os escopos exigidos continuam sendo verificados pela API.",
        }
        for methods in schema.get("paths", {}).values():
            for operation in methods.values():
                if not isinstance(operation, dict):
                    continue
                security = operation.get("security", [])
                if any(
                    "OAuth2PasswordBearer" in requirement for requirement in security
                ):
                    # Entradas separadas significam alternativas (OR), não dois tokens obrigatórios.
                    if {"BearerToken": []} not in security:
                        security.append({"BearerToken": []})
        return schema

    app.openapi = openapi
