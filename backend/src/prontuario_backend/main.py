import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse, Response

from prontuario_backend.config.http import SecurityMiddleware
from prontuario_backend.config.settings import get_settings
from prontuario_backend.config.swagger import swagger_config
from prontuario_backend.routes.api import router
from prontuario_backend.views.errors import error_body


def create_app():
    settings = get_settings()
    production = settings.app_env == "production"
    logging.getLogger("prontuario.requests").setLevel(logging.INFO)
    if not logging.getLogger("prontuario.requests").handlers:
        logging.getLogger("prontuario.requests").addHandler(logging.StreamHandler())
    app = FastAPI(**swagger_config(settings))
    app.add_middleware(SecurityMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc):
        message = (
            exc.detail if isinstance(exc.detail, str) else "Requisição não concluída"
        )
        return JSONResponse(
            error_body(f"http_{exc.status_code}", request.state.request_id, message),
            exc.status_code,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc):
        # Never echo invalid input values, which may contain credentials or records.
        return JSONResponse(
            error_body("validation_error", request.state.request_id), 422
        )

    app.include_router(router)
    if not production:

        @app.get("/metrics", include_in_schema=False)
        def metrics():
            registry = getattr(app.state, "metrics", None)
            return Response(
                generate_latest(registry) if registry else b"",
                media_type=CONTENT_TYPE_LATEST,
            )

    return app


app = create_app()
