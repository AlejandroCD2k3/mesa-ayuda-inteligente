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
        f"sqlite:///{(tmp_path / 'permisos.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", motor)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        motor.dispose()


def headers(cliente, identidad):
    token = cliente.post(
        "/api/demo/sesion",
        json={"usuario_id": identidad},
    ).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def crear(cliente, credencial, asunto="No puedo adjuntar una tarea"):
    return cliente.post(
        "/api/tickets",
        headers=credencial,
        json={
            "origen_sistema": "MAIA",
            "asunto": asunto,
            "descripcion": "Necesito ayuda con mi actividad.",
            "solicitante": "estudiante.alterno",
        },
    )


def test_rutas_protegidas_exigen_sesion(cliente):
    assert cliente.get("/api/tickets").status_code == 401
    assert cliente.get("/api/tickets/1").status_code == 401
    assert cliente.post(
        "/api/tickets",
        json={
            "origen_sistema": "MAIA",
            "asunto": "Problema",
            "descripcion": "No funciona",
        },
    ).status_code == 401


def test_estudiantes_aislados_y_sin_suplantacion(cliente):
    a = headers(cliente, "estudiante.demo")
    b = headers(cliente, "estudiante.alterno")

    primero = crear(cliente, a).json()
    segundo = crear(cliente, b, "Otra solicitud").json()

    assert primero["solicitante"] == "estudiante.demo"
    assert segundo["solicitante"] == "estudiante.alterno"

    listado_a = cliente.get("/api/tickets", headers=a).json()
    listado_b = cliente.get("/api/tickets", headers=b).json()

    assert [t["id"] for t in listado_a] == [primero["id"]]
    assert [t["id"] for t in listado_b] == [segundo["id"]]

    ruta = f"/api/tickets/{segundo['id']}"

    assert cliente.get(ruta, headers=a).status_code == 404
    assert cliente.patch(
        ruta,
        headers=a,
        json={"asunto": "Modificacion ajena"},
    ).status_code == 404


def test_soporte_separado_por_equipo(cliente):
    estudiante = headers(cliente, "estudiante.demo")
    funcional = headers(cliente, "soporte.funcional")
    tecnico = headers(cliente, "soporte.tecnico")

    f = crear(cliente, estudiante).json()
    t = crear(
        cliente, estudiante, "Error HTTP 500 de Moodle"
    ).json()

    cola_funcional = cliente.get(
        "/api/tickets", headers=funcional
    ).json()
    cola_tecnica = cliente.get(
        "/api/tickets", headers=tecnico
    ).json()

    assert [x["id"] for x in cola_funcional] == [f["id"]]
    assert [x["id"] for x in cola_tecnica] == [t["id"]]

    assert cliente.get(
        f"/api/tickets/{t['id']}", headers=funcional
    ).status_code == 404

    assert cliente.post(
        f"/api/tickets/{t['id']}/resolver",
        headers=funcional,
        json={"respuesta": "No autorizado"},
    ).status_code == 404

    assert cliente.post(
        f"/api/tickets/{f['id']}/resolver",
        headers=estudiante,
        json={"respuesta": "No autorizado"},
    ).status_code == 403

    assert cliente.post(
        f"/api/tickets/{f['id']}/resolver",
        headers=funcional,
        json={"respuesta": "Caso funcional atendido"},
    ).status_code == 200

    assert cliente.post(
        f"/api/tickets/{t['id']}/resolver",
        headers=tecnico,
        json={"respuesta": "Caso tecnico atendido"},
    ).status_code == 200


def test_soporte_no_puede_crear_ni_confirmar(cliente):
    soporte = headers(cliente, "soporte.funcional")
    estudiante = headers(cliente, "estudiante.demo")

    assert crear(cliente, soporte).status_code == 403

    auto = crear(
        cliente, estudiante,
        "Donde encuentro mis actividades en MAIA"
    ).json()

    assert auto["estado"] == "PENDIENTE_CONFIRMACION"

    assert cliente.post(
        f"/api/tickets/{auto['id']}/confirmacion",
        headers=soporte,
        json={"resuelta": True},
    ).status_code == 403


def test_no_confirmar_ticket_ajeno(cliente):
    a = headers(cliente, "estudiante.demo")
    b = headers(cliente, "estudiante.alterno")

    ticket = crear(
        cliente, a, "Donde encuentro mis actividades en MAIA"
    ).json()

    assert cliente.post(
        f"/api/tickets/{ticket['id']}/confirmacion",
        headers=b,
        json={"resuelta": True},
    ).status_code == 404


def test_tickets_anteriores_no_se_pierden(cliente):
    with Session(database.engine) as sesion:
        sesion.add(Ticket(
            origen_sistema="MAIA",
            solicitante="usuario.demo",
            asunto="Ticket anterior",
            descripcion="Solicitud registrada antes de la fase 5",
        ))
        sesion.commit()

    principal = headers(cliente, "estudiante.demo")
    alterno = headers(cliente, "estudiante.alterno")

    tickets_principal = cliente.get(
        "/api/tickets", headers=principal
    ).json()

    tickets_alterno = cliente.get(
        "/api/tickets", headers=alterno
    ).json()

    assert any(
        x["asunto"] == "Ticket anterior"
        for x in tickets_principal
    )
    assert all(
        x["asunto"] != "Ticket anterior"
        for x in tickets_alterno
    )
