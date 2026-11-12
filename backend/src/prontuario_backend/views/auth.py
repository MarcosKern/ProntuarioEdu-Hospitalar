from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IdentityResponse(BaseModel):
    subject: str


class SessionResponse(BaseModel):
    authenticated: Literal[True] = True
    subject: str
    expires_at: datetime
    expires_in_seconds: int = Field(ge=0)
    refresh_required: bool
