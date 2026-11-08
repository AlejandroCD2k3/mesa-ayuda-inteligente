from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from .clasificacion import clasificar_ticket
from .database import get_session, init_db
from .models import Ticket, ahora_utc
from .schemas import TicketCreate, TicketUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Mesa de Ayuda Inteligente",
    lifespan=lifespan,
)


@app.get("/api/health", include_in_schema=False)
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/tickets", response_model=Ticket, status_code=201)
def crear_ticket(
    datos: TicketCreate,
    session: Session = Depends(get_session),
):
    categoria, motivo = clasificar_ticket(
        datos.origen_sistema, datos.asunto, datos.descripcion
    )
    ticket = Ticket(
        **datos.model_dump(),
        categoria=categoria,
        motivo_clasificacion=motivo,
    )

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return ticket


@app.get("/api/tickets", response_model=list[Ticket])
def listar_tickets(session: Session = Depends(get_session)):
    return session.exec(
        select(Ticket).order_by(Ticket.id)
    ).all()


@app.get("/api/tickets/{ticket_id}", response_model=Ticket)
def obtener_ticket(
    ticket_id: int,
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    return ticket


@app.patch("/api/tickets/{ticket_id}", response_model=Ticket)
def actualizar_ticket(
    ticket_id: int,
    datos: TicketUpdate,
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(ticket, campo, valor)

    ticket.categoria, ticket.motivo_clasificacion = clasificar_ticket(
        ticket.origen_sistema, ticket.asunto, ticket.descripcion
    )
    ticket.fecha_actualizacion = ahora_utc()

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return ticket
