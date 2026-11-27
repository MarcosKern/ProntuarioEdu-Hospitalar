from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContextoAssistencialCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        json_schema_extra={
            "examples": [
                {
                    "codigo": "CTX-TESTE-01",
                    "nome": "Consulta simulada",
                    "tipo_atendimento": "consulta",
                }
            ]
        },
    )

    codigo: str = Field(max_length=45)
    nome: str = Field(max_length=120)
    tipo_atendimento: str = Field(max_length=30)
    nivel_cuidado: str | None = Field(default=None, max_length=50)


class ContextoAssistencialPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: str = Field(default=None, max_length=120)
    tipo_atendimento: str = Field(default=None, max_length=30)
    nivel_cuidado: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError(
                "Informe ao menos nome, tipo de atendimento ou nível de cuidado"
            )
        return self


class ContextoAssistencialResponse(BaseModel):
    id: UUID
    codigo: str
    nome: str
    tipo_atendimento: str
    nivel_cuidado: str | None
    ativo: int
    criado_em: datetime
