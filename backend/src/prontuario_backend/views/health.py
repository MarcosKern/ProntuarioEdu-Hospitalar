from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str


def health_response():
    return HealthResponse(status="ok", database="ok")
