from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]


def health_response():
    return HealthResponse(status="ok", database="ok")
