from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class CategoriaTicket(str, Enum):
    AUTO = "AUTO"
    FUNCIONAL = "FUNCIONAL"
    TECNICO = "TÉCNICO"


class EstadoTicket(str, Enum):
    ABIERTO = "ABIERTO"
    PENDIENTE_CONFIRMACION = "PENDIENTE_CONFIRMACION"
    EN_ATENCION = "EN_ATENCION"
    RESUELTO = "RESUELTO"


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    id: int | None = Field(default=None, primary_key=True)

    origen_sistema: str
    solicitante: str
    asunto: str
    descripcion: str

    categoria: CategoriaTicket | None = Field(default=None)
    estado: EstadoTicket = Field(default=EstadoTicket.ABIERTO)
    responsable: str | None = Field(default=None)

    motivo_clasificacion: str | None = Field(default=None)
    respuesta_sugerida: str | None = Field(default=None)
    respuesta_atencion: str | None = Field(default=None)

    fecha_creacion: datetime = Field(default_factory=ahora_utc)
    fecha_actualizacion: datetime = Field(default_factory=ahora_utc)
