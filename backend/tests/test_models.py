from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.models import CategoriaTicket, EstadoTicket, Ticket


def test_ticket_inicial():
    ticket = Ticket(
        origen_sistema="MAIA",
        solicitante="usuario.demo",
        asunto="Consulta de acceso",
        descripcion="No encuentro una opción en MAIA.",
    )

    assert ticket.id is None
    assert ticket.categoria is None
    assert ticket.estado == EstadoTicket.ABIERTO
    assert ticket.responsable is None
    assert ticket.fecha_creacion is not None


def test_persistencia_sqlite(tmp_path: Path):
    ruta = tmp_path / "prueba.db"
    engine = create_engine(f"sqlite:///{ruta.as_posix()}")

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        ticket = Ticket(
            origen_sistema="EvaluIA",
            solicitante="usuario.demo",
            asunto="Error al conectar con Moodle",
            descripcion="El servicio devuelve HTTP 500.",
            categoria=CategoriaTicket.TECNICO,
            estado=EstadoTicket.EN_ATENCION,
            responsable="soporte_tecnico",
            motivo_clasificacion="Error de integración HTTP 500.",
        )

        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        identificador = ticket.id
        assert identificador is not None

    with Session(engine) as session:
        guardado = session.get(Ticket, identificador)

        assert guardado is not None
        assert guardado.origen_sistema == "EvaluIA"
        assert guardado.categoria == CategoriaTicket.TECNICO
        assert guardado.estado == EstadoTicket.EN_ATENCION
        assert guardado.responsable == "soporte_tecnico"
