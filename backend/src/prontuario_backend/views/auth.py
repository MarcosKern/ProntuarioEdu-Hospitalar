from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr

MAX_SCOPE_LENGTH = 512


class IdentityResponse(BaseModel):
    subject: UUID


class AdministratorResponse(IdentityResponse):
    user_id: UUID
    login: str
    name: str
    profile: Literal["ADMINISTRADOR"] = "ADMINISTRADOR"
    permissions: list[str] = Field(default_factory=lambda: ["USUARIO_GERENCIAR"])


class SessionResponse(BaseModel):
    authenticated: Literal[True] = True
    subject: UUID
    expires_at: datetime
    expires_in_seconds: int = Field(ge=0)
    refresh_required: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)
    scope: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    grant_type: Literal["password"]
    username: str = Field(min_length=1, max_length=150)
    password: SecretStr = Field(min_length=1, max_length=128)
    scope: str = Field(default="", max_length=MAX_SCOPE_LENGTH)
    client_id: Literal[""] = Field(default="", description="Login local: deixar vazio")
    client_secret: Literal[""] = Field(
        default="", repr=False, description="Login local: deixar vazio"
    )


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    refresh_token: SecretStr = Field(min_length=1, max_length=200)
    scope: str = Field(default="identity:read", max_length=MAX_SCOPE_LENGTH)


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)
