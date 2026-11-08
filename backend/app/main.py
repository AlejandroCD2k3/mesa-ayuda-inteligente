from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from .clasificacion import clasificar_ticket
from .sesiones_demo import UsuarioDemo, obtener_usuario_demo, router as router_demo
from .database import get_session, init_db
from .soluciones import sugerir_solucion
from .models import CategoriaTicket, EstadoTicket, Ticket, ahora_utc
from .schemas import ConfirmacionSolucion, RespuestaAtencion, TicketCreate, TicketUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Mesa de Ayuda Inteligente",
    lifespan=lifespan,
)

app.include_router(router_demo)


# Tickets creados durante los hitos anteriores.
# Permanecen sin cambios en SQLite.
_LEGADOS = ("usuario.demo", "estudiante.pruebas")


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
    propios = (usuario.id,)
    if usuario.id == "estudiante.demo":
        propios += _LEGADOS
    return propios


def puede_ver(ticket: Ticket, usuario: UsuarioDemo) -> bool:
    if usuario.rol == "estudiante":
        return ticket.solicitante in solicitantes_visibles(usuario)

    return ticket.responsable == usuario.rol


def exigir_acceso(ticket: Ticket, usuario: UsuarioDemo) -> None:
    if not puede_ver(ticket, usuario):
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado",
        )


@app.get("/api/health", include_in_schema=False)
@app.get("/health")
def health():
    return {"status": "ok"}


def preparar_ticket(ticket: Ticket) -> None:
    categoria, motivo = clasificar_ticket(
        ticket.origen_sistema, ticket.asunto, ticket.descripcion
    )

    ticket.categoria = categoria
    ticket.motivo_clasificacion = motivo
    ticket.respuesta_sugerida = sugerir_solucion(categoria)

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

@app.post("/api/tickets", response_model=Ticket, status_code=201)
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

    preparar_ticket(ticket)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return ticket


@app.get("/api/tickets", response_model=list[Ticket])
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


@app.get("/api/tickets/{ticket_id}", response_model=Ticket)
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


@app.patch("/api/tickets/{ticket_id}", response_model=Ticket)
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

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(ticket, campo, valor)

    preparar_ticket(ticket)
    ticket.fecha_actualizacion = ahora_utc()

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return ticket

@app.post("/api/tickets/{ticket_id}/confirmacion", response_model=Ticket)
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
    session.commit()
    session.refresh(ticket)

    return ticket


@app.post("/api/tickets/{ticket_id}/resolver", response_model=Ticket)
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
    session.commit()
    session.refresh(ticket)

    return ticket
