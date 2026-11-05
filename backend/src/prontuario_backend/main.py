from fastapi import FastAPI

from prontuario_backend.routes.api import router

app = FastAPI(
    title="ProntuarioEdu — desenvolvimento", version="0.1.0",
    swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": True},
)
app.include_router(router)
