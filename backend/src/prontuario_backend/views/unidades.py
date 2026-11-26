from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UnidadeCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        json_schema_extra={
            "examples": [
                {
                    "codigo": "UN-TESTE-01",
                    "nome": "Unidade Escola",
                    "tipo": "ensino",
                }
            ]
        },
    )

    codigo: str = Field(max_length=30)
    nome: str = Field(max_length=120)
    tipo: str = Field(max_length=40)


class UnidadePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: str = Field(default=None, max_length=120)
    tipo: str = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        return self


class UnidadeResponse(BaseModel):
    id: UUID
    codigo: str
    nome: str
    tipo: str
    ativo: int
    criado_em: datetime
