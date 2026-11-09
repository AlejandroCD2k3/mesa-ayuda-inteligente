"""Adaptador HTTP para tickets."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..application.tickets import preparar_ticket as _preparar_ticket, registrar_evento
from ..database import get_session
from ..domain.permisos import solicitantes_visibles as _solicitantes_visibles, puede_ver as _puede_ver
from ..ia import analizar_ticket_con_ia
from ..models import CategoriaTicket, EstadoTicket, Ticket, TicketEvento, ahora_utc
from ..schemas import ConfirmacionSolucion, RespuestaAtencion, TicketCreate, TicketUpdate
from ..sesiones_demo import UsuarioDemo, obtener_usuario_demo

router = APIRouter(tags=["Tickets"])


def preparar_ticket(ticket: Ticket, session: Session | None = None) -> None:
    _preparar_ticket(ticket, session, analizador=analizar_ticket_con_ia)


# Tickets creados durante los hitos anteriores.
# Permanecen sin cambios en SQLite.


def solo_estudiante(usuario: UsuarioDemo) -> None:
    if usuario.rol != "estudiante":
        raise HTTPException(
            status_code=403,
            detail="Operacion reservada a estudiantes.",
        )


def solo_soporte(usuario: UsuarioDemo) -> None:
    if usuario.rol not in (
        "soporte_funcional", "soporte_tecnico"
    ):
        raise HTTPException(
            status_code=403,
            detail="Operacion reservada a soporte.",
        )


def solicitantes_visibles(usuario: UsuarioDemo) -> tuple[str, ...]:
    return _solicitantes_visibles(usuario.id)


def puede_ver(ticket: Ticket, usuario: UsuarioDemo) -> bool:
    return _puede_ver(usuario.rol, usuario.id, ticket.solicitante, ticket.responsable)


def exigir_acceso(ticket: Ticket, usuario: UsuarioDemo) -> None:
    if not puede_ver(ticket, usuario):
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado",
        )


@router.post("/api/tickets", response_model=Ticket, status_code=201)
def crear_ticket(
    datos: TicketCreate,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    solo_estudiante(usuario)

    ticket = Ticket(
        **datos.model_dump(exclude={"solicitante"}),
        solicitante=usuario.id,
    )

    preparar_ticket(ticket, session)

    session.add(ticket)
    session.flush()

    registrar_evento(
        session, ticket, "CREACION",
        "Solicitud registrada.", usuario.id,
    )

    registrar_evento(
        session, ticket, "CLASIFICACION",
        f"Clasificado como {ticket.categoria.value}.",
        "sistema",
    )

    if ticket.responsable:
        registrar_evento(
            session, ticket, "ASIGNACION",
            f"Asignado a {ticket.responsable}.",
            "sistema",
        )

    session.commit()
    session.refresh(ticket)

    return ticket


@router.get("/api/tickets", response_model=list[Ticket])
def listar_tickets(
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    consulta = select(Ticket).order_by(Ticket.id)

    if usuario.rol == "estudiante":
        consulta = consulta.where(
            Ticket.solicitante.in_(solicitantes_visibles(usuario))
        )
    else:
        consulta = consulta.where(
            Ticket.responsable == usuario.rol
        )

    return session.exec(consulta).all()


@router.get("/api/tickets/{ticket_id}", response_model=Ticket)
def obtener_ticket(
    ticket_id: int,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    exigir_acceso(ticket, usuario)

    return ticket


@router.get("/api/tickets/{ticket_id}/eventos", response_model=list[TicketEvento])
def listar_eventos(
    ticket_id: int,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado",
        )

    exigir_acceso(ticket, usuario)

    return session.exec(
        select(TicketEvento)
        .where(TicketEvento.ticket_id == ticket_id)
        .order_by(TicketEvento.id)
    ).all()


@router.patch("/api/tickets/{ticket_id}", response_model=Ticket)
def actualizar_ticket(
    ticket_id: int,
    datos: TicketUpdate,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    solo_estudiante(usuario)
    exigir_acceso(ticket, usuario)

    if (
        ticket.estado not in (EstadoTicket.ABIERTO, EstadoTicket.EN_ATENCION)
        or ticket.respuesta_sugerida
    ):
        raise HTTPException(
            status_code=409,
            detail="El ticket no admite ediciones en su estado actual.",
        )

    categoria_anterior = ticket.categoria
    responsable_anterior = ticket.responsable

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(ticket, campo, valor)

    preparar_ticket(ticket)
    ticket.fecha_actualizacion = ahora_utc()

    session.add(ticket)

    registrar_evento(
        session, ticket, "ACTUALIZACION",
        "El solicitante actualizo los datos del ticket.",
        usuario.id,
    )

    if ticket.categoria != categoria_anterior:
        registrar_evento(
            session, ticket, "CLASIFICACION",
            f"Reclasificado como {ticket.categoria.value}.",
            "sistema",
        )

    if ticket.responsable and ticket.responsable != responsable_anterior:
        registrar_evento(
            session, ticket, "ASIGNACION",
            f"Asignado a {ticket.responsable}.",
            "sistema",
        )

    session.commit()
    session.refresh(ticket)

    return ticket

@router.post("/api/tickets/{ticket_id}/confirmacion", response_model=Ticket)
def confirmar_solucion(
    ticket_id: int,
    datos: ConfirmacionSolucion,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    solo_estudiante(usuario)
    exigir_acceso(ticket, usuario)

    if (
        ticket.categoria != CategoriaTicket.AUTO
        or ticket.estado != EstadoTicket.PENDIENTE_CONFIRMACION
        or not ticket.respuesta_sugerida
    ):
        raise HTTPException(
            status_code=409,
            detail="El ticket no tiene una solucion pendiente de confirmacion.",
        )

    if datos.resuelta:
        ticket.estado = EstadoTicket.RESUELTO
    else:
        ticket.categoria = CategoriaTicket.FUNCIONAL
        ticket.estado = EstadoTicket.EN_ATENCION
        ticket.responsable = "soporte_funcional"
        ticket.motivo_clasificacion = (
            "La solucion automatica fue rechazada por el solicitante; "
            "se remite a atencion funcional."
        )

    ticket.fecha_actualizacion = ahora_utc()

    session.add(ticket)

    if datos.resuelta:
        registrar_evento(
            session, ticket, "CONFIRMACION",
            "El solicitante confirmo que la solucion funciono.",
            usuario.id,
        )
    else:
        registrar_evento(
            session, ticket, "ESCALAMIENTO",
            "La sugerencia fue rechazada y se remitio a soporte funcional.",
            usuario.id,
        )

    session.commit()
    session.refresh(ticket)

    return ticket


@router.post("/api/tickets/{ticket_id}/resolver", response_model=Ticket)
def resolver_ticket(
    ticket_id: int,
    datos: RespuestaAtencion,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    solo_soporte(usuario)
    exigir_acceso(ticket, usuario)

    if (
        ticket.estado != EstadoTicket.EN_ATENCION
        or ticket.categoria not in (
            CategoriaTicket.FUNCIONAL,
            CategoriaTicket.TECNICO,
        )
        or not ticket.responsable
    ):
        raise HTTPException(
            status_code=409,
            detail="El ticket no se encuentra en atencion humana.",
        )

    ticket.respuesta_atencion = datos.respuesta
    ticket.estado = EstadoTicket.RESUELTO
    ticket.fecha_actualizacion = ahora_utc()

    session.add(ticket)

    registrar_evento(
        session, ticket, "RESOLUCION",
        "Soporte registro la respuesta y resolvio la solicitud.",
        usuario.id,
    )

    session.commit()
    session.refresh(ticket)

    return ticket
