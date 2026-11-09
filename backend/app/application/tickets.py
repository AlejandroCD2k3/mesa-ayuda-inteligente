"""Casos de uso de clasificación y eventos."""
from sqlmodel import Session
from ..domain.clasificacion import clasificar_ticket
from ..domain.soluciones import sugerir_solucion
from ..models import CategoriaTicket, EstadoTicket, Ticket, TicketEvento


def preparar_ticket(ticket: Ticket, session: Session | None = None, analizador=None) -> None:
    categoria, motivo = clasificar_ticket(
        ticket.origen_sistema, ticket.asunto, ticket.descripcion
    )

    respuesta = sugerir_solucion(categoria)

    if session is not None and analizador is not None:
        resultado_ia = analizador(session, ticket)

        if resultado_ia is not None:
            categoria, motivo, respuesta = resultado_ia

    ticket.categoria = categoria
    ticket.motivo_clasificacion = motivo
    ticket.respuesta_sugerida = respuesta

    if ticket.respuesta_sugerida:
        ticket.estado = EstadoTicket.PENDIENTE_CONFIRMACION
        ticket.responsable = None
    else:
        ticket.estado = EstadoTicket.EN_ATENCION
        ticket.responsable = (
            "soporte_tecnico"
            if categoria == CategoriaTicket.TECNICO
            else "soporte_funcional"
        )

def registrar_evento(
    session: Session,
    ticket: Ticket,
    tipo: str,
    detalle: str,
    actor: str,
) -> None:
    if ticket.id is None:
        raise RuntimeError("El ticket debe tener identificador.")

    session.add(TicketEvento(
        ticket_id=ticket.id,
        tipo=tipo,
        detalle=detalle,
        actor=actor,
    ))
