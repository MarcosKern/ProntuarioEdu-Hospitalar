from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from prontuario_backend.views.pagination import PaginationParams


class MedicamentoCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        json_schema_extra={
            "examples": [
                {
                    "nome": "Medicamento de demonstração",
                    "forma_farmaceutica": "comprimido",
                }
            ]
        },
    )

    nome: str = Field(max_length=160)
    principio_ativo: str | None = Field(default=None, max_length=160)
    nome_comercial: str | None = Field(default=None, max_length=160)
    forma_farmaceutica: str | None = Field(default=None, max_length=80)
    descricao: str | None = None


class MedicamentoPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: str = Field(default=None, max_length=160)
    principio_ativo: str | None = Field(default=None, max_length=160)
    nome_comercial: str | None = Field(default=None, max_length=160)
    forma_farmaceutica: str | None = Field(default=None, max_length=80)
    descricao: str | None = None

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        return self


class MedicamentoListQuery(PaginationParams):
    nome: str | None = Field(
        default=None,
        description="Substring literal do nome; % e _ são tratados como caracteres",
    )


class MedicamentoResponse(BaseModel):
    id: UUID
    nome: str
    principio_ativo: str | None
    nome_comercial: str | None
    forma_farmaceutica: str | None
    descricao: str | None
    ativo: int
    criado_em: datetime
