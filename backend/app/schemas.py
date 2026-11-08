from pydantic import BaseModel, ConfigDict, Field, model_validator


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    origen_sistema: str = Field(min_length=1)
    solicitante: str = Field(min_length=1)
    asunto: str = Field(min_length=1)
    descripcion: str = Field(min_length=1)


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    asunto: str | None = Field(default=None, min_length=1)
    descripcion: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validar_cambios(self):
        cambios = self.model_dump(exclude_unset=True)

        if not cambios or any(valor is None for valor in cambios.values()):
            raise ValueError("Indica al menos un campo con texto.")

        return self


class ConfirmacionSolucion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    resuelta: bool


class RespuestaAtencion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    respuesta: str = Field(min_length=1)
