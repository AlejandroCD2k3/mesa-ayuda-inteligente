from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app import database
from app.main import app
from app.models import Ticket


@pytest.fixture
def cliente(tmp_path: Path, monkeypatch):
    motor = create_engine(
        f"sqlite:///{(tmp_path / 'historial.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", motor)

    try:
        with TestClient(app) as c:
            yield c
    finally:
        motor.dispose()


def acceso(c, identidad):
    sesion = c.post(
        "/api/demo/sesion",
        json={"usuario_id": identidad},
    ).json()

    return {"Authorization": f"Bearer {sesion['token']}"}


def crear(c, headers, asunto="No puedo adjuntar una tarea"):
    respuesta = c.post(
        "/api/tickets",
        headers=headers,
        json={
            "origen_sistema": "MAIA",
            "asunto": asunto,
            "descripcion": "Necesito ayuda con la actividad.",
        },
    )

    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def consultar(c, headers, ticket):
    respuesta = c.get(
        f"/api/tickets/{ticket['id']}/eventos",
        headers=headers,
    )

    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_creacion_clasificacion_y_asignacion(cliente):
    estudiante = acceso(cliente, "estudiante.demo")
    ticket = crear(cliente, estudiante)
    eventos = consultar(cliente, estudiante, ticket)

    assert [e["tipo"] for e in eventos] == [
        "CREACION", "CLASIFICACION", "ASIGNACION"
    ]

    assert eventos[0]["actor"] == "estudiante.demo"
    assert eventos[1]["actor"] == "sistema"
    assert all(e["fecha"] for e in eventos)
    assert [e["id"] for e in eventos] == sorted(
        e["id"] for e in eventos
    )


def test_edicion_con_reclasificacion(cliente):
    estudiante = acceso(cliente, "estudiante.demo")
    ticket = crear(cliente, estudiante)

    respuesta = cliente.patch(
        f"/api/tickets/{ticket['id']}",
        headers=estudiante,
        json={
            "descripcion": "Error HTTP 500 del servidor Moodle."
        },
    )

    assert respuesta.status_code == 200

    assert [e["tipo"] for e in consultar(
        cliente, estudiante, ticket
    )] == [
        "CREACION",
        "CLASIFICACION",
        "ASIGNACION",
        "ACTUALIZACION",
        "CLASIFICACION",
        "ASIGNACION",
    ]


def test_confirmacion_y_escalamiento(cliente):
    estudiante = acceso(cliente, "estudiante.demo")

    primero = crear(
        cliente, estudiante,
        "Donde encuentro mis actividades en MAIA",
    )

    segundo = crear(
        cliente, estudiante,
        "Como consultar actividades en MAIA",
    )

    assert cliente.post(
        f"/api/tickets/{primero['id']}/confirmacion",
        headers=estudiante,
        json={"resuelta": True},
    ).status_code == 200

    assert cliente.post(
        f"/api/tickets/{segundo['id']}/confirmacion",
        headers=estudiante,
        json={"resuelta": False},
    ).status_code == 200

    assert consultar(
        cliente, estudiante, primero
    )[-1]["tipo"] == "CONFIRMACION"

    assert consultar(
        cliente, estudiante, segundo
    )[-1]["tipo"] == "ESCALAMIENTO"


def test_soporte_resuelve_y_conserva_historial(cliente):
    estudiante = acceso(cliente, "estudiante.demo")
    soporte = acceso(cliente, "soporte.funcional")

    ticket = crear(cliente, estudiante)

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        headers=soporte,
        json={"respuesta": "Se restablecio el acceso."},
    )

    assert respuesta.status_code == 200

    eventos = consultar(cliente, estudiante, ticket)

    assert eventos[-1]["tipo"] == "RESOLUCION"
    assert eventos[-1]["actor"] == "soporte.funcional"

    assert consultar(
        cliente, soporte, ticket
    )[-1]["tipo"] == "RESOLUCION"


def test_historial_respetando_permisos(cliente):
    estudiante_a = acceso(cliente, "estudiante.demo")
    estudiante_b = acceso(cliente, "estudiante.alterno")
    tecnico = acceso(cliente, "soporte.tecnico")

    ticket = crear(cliente, estudiante_a)
    ruta = f"/api/tickets/{ticket['id']}/eventos"

    assert cliente.get(ruta).status_code == 401
    assert cliente.get(
        ruta, headers=estudiante_b
    ).status_code == 404

    assert cliente.get(
        ruta, headers=tecnico
    ).status_code == 404

    assert cliente.get(
        "/api/tickets/99999/eventos",
        headers=estudiante_a,
    ).status_code == 404


def test_ticket_legacy_no_inventa_eventos(cliente):
    with Session(database.engine) as session:
        ticket = Ticket(
            origen_sistema="MAIA",
            solicitante="usuario.demo",
            asunto="Solicitud anterior",
            descripcion="Creada antes del historial",
        )

        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        identificador = ticket.id

    estudiante = acceso(cliente, "estudiante.demo")

    respuesta = cliente.get(
        f"/api/tickets/{identificador}/eventos",
        headers=estudiante,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == []
