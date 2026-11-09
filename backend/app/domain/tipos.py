from enum import Enum


class CategoriaTicket(str, Enum):
    AUTO = "AUTO"
    FUNCIONAL = "FUNCIONAL"
    TECNICO = "TÉCNICO"


class EstadoTicket(str, Enum):
    ABIERTO = "ABIERTO"
    PENDIENTE_CONFIRMACION = "PENDIENTE_CONFIRMACION"
    EN_ATENCION = "EN_ATENCION"
    RESUELTO = "RESUELTO"
