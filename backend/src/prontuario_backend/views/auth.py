from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class IdentityResponse(BaseModel):
    subject: str


class AdministratorResponse(IdentityResponse):
    user_id: str
    login: str
    name: str
    profile: Literal["ADMINISTRADOR"] = "ADMINISTRADOR"
    permissions: list[str] = Field(default_factory=lambda: ["USUARIO_GERENCIAR"])


class SessionResponse(BaseModel):
    authenticated: Literal[True] = True
    subject: str
    expires_at: datetime
    expires_in_seconds: int = Field(ge=0)
    refresh_required: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    scope: str


class RefreshRequest(BaseModel):
    refresh_token: SecretStr = Field(max_length=200)
    scope: str = "identity:read"


class PasswordChangeRequest(BaseModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)
