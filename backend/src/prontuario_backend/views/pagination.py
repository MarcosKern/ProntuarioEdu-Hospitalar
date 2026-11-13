"""Contratos para futuras listagens; não executam SQL nem criam endpoints."""
from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_OFFSET = 100000


class PaginationParams(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Quantidade máxima de itens")
    offset: int = Field(default=0, ge=0, le=MAX_OFFSET, description="Quantidade de itens a pular")


class PageResponse[Item](BaseModel):
    items: list[Item]
    total: int = Field(ge=0, description="Total de itens após os mesmos filtros e permissões da listagem")
    limit: int = Field(ge=1, le=MAX_LIMIT)
    offset: int = Field(ge=0, le=MAX_OFFSET)

    @model_validator(mode="after")
    def validate_page(self):
        if len(self.items) > self.limit or (self.items and self.offset + len(self.items) > self.total):
            raise ValueError("A página deve respeitar limit, offset e total")
        return self
