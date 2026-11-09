from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from ...domain.tipos import CategoriaTicket, EstadoTicket


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


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


class TicketEvento(SQLModel, table=True):
    __tablename__ = "ticket_eventos"

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="tickets.id", index=True)
    tipo: str
    detalle: str
    actor: str
    fecha: datetime = Field(default_factory=ahora_utc)


class ArticuloConocimiento(SQLModel, table=True):
    __tablename__ = "articulos_conocimiento"

    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    contenido: str
    categoria: CategoriaTicket
    publicado: bool = Field(default=True)
    creado_por: str
    fecha_creacion: datetime = Field(default_factory=ahora_utc)
    fecha_actualizacion: datetime = Field(default_factory=ahora_utc)
