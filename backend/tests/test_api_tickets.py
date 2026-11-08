from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from app import database
from app.main import app


@pytest.fixture
def cliente(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ruta = tmp_path / "tickets-api.db"

    motor_prueba = create_engine(
        f"sqlite:///{ruta.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    monkeypatch.setattr(database, "engine", motor_prueba)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        motor_prueba.dispose()


def datos_ticket():
    return {
        "origen_sistema": "MAIA",
        "solicitante": "usuario.demo",
        "asunto": "No puedo acceder",
        "descripcion": "El sistema no permite iniciar sesión.",
    }


def test_base_inicialmente_vacia(cliente):
    respuesta = cliente.get("/api/tickets")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_crear_ticket(cliente):
    respuesta = cliente.post("/api/tickets", json=datos_ticket())

    assert respuesta.status_code == 201

    ticket = respuesta.json()

    assert ticket["id"] is not None
    assert ticket["asunto"] == "No puedo acceder"
    assert ticket["categoria"] == "FUNCIONAL"
    assert ticket["estado"] == "ABIERTO"
    assert ticket["responsable"] is None
    assert ticket["fecha_creacion"] is not None


def test_listar_y_obtener_tickets(cliente):
    primero = cliente.post("/api/tickets", json=datos_ticket()).json()

    segundo_datos = datos_ticket()
    segundo_datos["asunto"] = "Otra solicitud"

    segundo = cliente.post("/api/tickets", json=segundo_datos).json()

    listado = cliente.get("/api/tickets")

    assert listado.status_code == 200
    assert [ticket["id"] for ticket in listado.json()] == [
        primero["id"],
        segundo["id"],
    ]

    detalle = cliente.get(f"/api/tickets/{segundo['id']}")

    assert detalle.status_code == 200
    assert detalle.json()["asunto"] == "Otra solicitud"


def test_actualizar_ticket(cliente):
    creado = cliente.post("/api/tickets", json=datos_ticket()).json()

    respuesta = cliente.patch(
        f"/api/tickets/{creado['id']}",
        json={"asunto": "Problema de autenticación"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["asunto"] == "Problema de autenticación"
    assert respuesta.json()["descripcion"] == creado["descripcion"]
    assert respuesta.json()["estado"] == "ABIERTO"

    guardado = cliente.get(f"/api/tickets/{creado['id']}").json()

    assert guardado["asunto"] == "Problema de autenticación"


def test_ticket_no_encontrado(cliente):
    assert cliente.get("/api/tickets/999").status_code == 404

    assert cliente.patch(
        "/api/tickets/999",
        json={"asunto": "Nuevo asunto"},
    ).status_code == 404


def test_validacion_de_datos(cliente):
    assert cliente.post(
        "/api/tickets",
        json={"asunto": "Incompleto"},
    ).status_code == 422

    assert cliente.post(
        "/api/tickets",
        json={**datos_ticket(), "asunto": "   "},
    ).status_code == 422

    assert cliente.post(
        "/api/tickets",
        json={**datos_ticket(), "estado": "RESUELTO"},
    ).status_code == 422

    creado = cliente.post("/api/tickets", json=datos_ticket()).json()
    ruta = f"/api/tickets/{creado['id']}"

    assert cliente.patch(ruta, json={}).status_code == 422
    assert cliente.patch(ruta, json={"asunto": None}).status_code == 422
    assert cliente.patch(ruta, json={"estado": "RESUELTO"}).status_code == 422


def test_health_mediante_api(cliente):
    respuesta = cliente.get("/api/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}

def test_clasificacion_al_crear_ticket(cliente):
    respuesta = cliente.post(
        "/api/tickets",
        json={
            "origen_sistema": "MAIA",
            "solicitante": "usuario.demo",
            "asunto": "¿Dónde encuentro mis actividades?",
            "descripcion": "Quiero consultar las actividades del curso.",
        },
    )

    assert respuesta.status_code == 201
    ticket = respuesta.json()

    assert ticket["categoria"] == "AUTO"
    assert ticket["motivo_clasificacion"]
    assert ticket["estado"] == "ABIERTO"


def test_reclasificacion_al_editar_ticket(cliente):
    creado = cliente.post(
        "/api/tickets",
        json={
            "origen_sistema": "EvaluIA",
            "solicitante": "usuario.demo",
            "asunto": "Consulta de acceso",
            "descripcion": "Necesito ayuda para entrar.",
        },
    ).json()

    assert creado["categoria"] == "FUNCIONAL"

    respuesta = cliente.patch(
        f"/api/tickets/{creado['id']}",
        json={"descripcion": "El servidor devuelve HTTP 500 al conectar Moodle."},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["categoria"] == "TÉCNICO"
    assert respuesta.json()["motivo_clasificacion"]

    guardado = cliente.get(f"/api/tickets/{creado['id']}").json()
    assert guardado["categoria"] == "TÉCNICO"
