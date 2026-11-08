from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from app import database
from app.main import app


@pytest.fixture
def cliente_aceptacion(tmp_path: Path, monkeypatch):
    ruta = tmp_path / "aceptacion.db"
    motor = create_engine(
        f"sqlite:///{ruta.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    monkeypatch.setattr(database, "engine", motor)

    try:
        with TestClient(app) as cliente:
            sesion = cliente.post(
                "/api/demo/sesion",
                json={"usuario_id": "estudiante.demo"},
            ).json()
            cliente.headers.update({
                "Authorization": f"Bearer {sesion['token']}"
            })
            yield cliente
    finally:
        motor.dispose()


def cabeceras_soporte(cliente, tecnico=False):
    identidad = (
        "soporte.tecnico" if tecnico else "soporte.funcional"
    )
    sesion = cliente.post(
        "/api/demo/sesion",
        json={"usuario_id": identidad},
    ).json()
    return {"Authorization": f"Bearer {sesion['token']}"}


def registrar(cliente, asunto, descripcion, sistema="MAIA"):
    respuesta = cliente.post(
        "/api/tickets",
        json={
            "origen_sistema": sistema,
            "solicitante": "estudiante.pruebas",
            "asunto": asunto,
            "descripcion": descripcion,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def consultar(cliente, ticket):
    respuesta = cliente.get(f"/api/tickets/{ticket['id']}")
    assert respuesta.status_code == 200
    return respuesta.json()


def test_aceptacion_01_solucion_automatica_aceptada(cliente_aceptacion):
    cliente = cliente_aceptacion

    ticket = registrar(
        cliente,
        "¿Dónde encuentro mis actividades?",
        "Quiero consultar las actividades del curso.",
    )

    assert ticket["categoria"] == "AUTO"
    assert ticket["estado"] == "PENDIENTE_CONFIRMACION"
    assert ticket["respuesta_sugerida"]
    assert ticket["motivo_clasificacion"]

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/confirmacion",
        json={"resuelta": True},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RESUELTO"
    assert consultar(cliente, ticket)["estado"] == "RESUELTO"


def test_aceptacion_02_rechazo_y_escalamiento(cliente_aceptacion):
    cliente = cliente_aceptacion

    ticket = registrar(
        cliente,
        "¿Dónde encuentro mis actividades?",
        "Quiero consultar las actividades del curso.",
    )

    rechazo = cliente.post(
        f"/api/tickets/{ticket['id']}/confirmacion",
        json={"resuelta": False},
    )

    assert rechazo.status_code == 200
    assert rechazo.json()["categoria"] == "FUNCIONAL"
    assert rechazo.json()["estado"] == "EN_ATENCION"
    assert rechazo.json()["responsable"] == "soporte_funcional"

    cierre = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        json={
            "respuesta": "Se acompano al estudiante y se verifico el acceso."
        },
        headers=cabeceras_soporte(cliente),
    )

    assert cierre.status_code == 200
    assert cierre.json()["estado"] == "RESUELTO"

    guardado = consultar(cliente, ticket)
    assert guardado["respuesta_sugerida"]
    assert guardado["respuesta_atencion"]


def test_aceptacion_03_atencion_funcional_directa(cliente_aceptacion):
    cliente = cliente_aceptacion

    ticket = registrar(
        cliente,
        "No puedo adjuntar una tarea",
        "Necesito ayuda para entregar mi actividad.",
    )

    assert ticket["categoria"] == "FUNCIONAL"
    assert ticket["estado"] == "EN_ATENCION"
    assert ticket["responsable"] == "soporte_funcional"
    assert ticket["respuesta_sugerida"] is None

    cierre = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        json={"respuesta": "Se reviso y restablecio la entrega."},
        headers=cabeceras_soporte(cliente),
    )

    assert cierre.status_code == 200
    assert consultar(cliente, ticket)["estado"] == "RESUELTO"


def test_aceptacion_04_atencion_tecnica_directa(cliente_aceptacion):
    cliente = cliente_aceptacion

    ticket = registrar(
        cliente,
        "Error HTTP 500 entre EvaluIA y Moodle",
        "Fallo de integracion al consultar el servicio.",
        sistema="EvaluIA",
    )

    assert ticket["categoria"] == "TÉCNICO"
    assert ticket["estado"] == "EN_ATENCION"
    assert ticket["responsable"] == "soporte_tecnico"

    cierre = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        json={"respuesta": "Se restablecio el servicio de integracion."},
        headers=cabeceras_soporte(cliente, tecnico=True),
    )

    assert cierre.status_code == 200

    guardado = consultar(cliente, ticket)
    assert guardado["estado"] == "RESUELTO"
    assert guardado["respuesta_atencion"]


def test_aceptacion_05_operaciones_invalidas(cliente_aceptacion):
    cliente = cliente_aceptacion

    auto = registrar(
        cliente,
        "¿Dónde encuentro mis actividades?",
        "Quiero consultar las actividades del curso.",
    )

    ruta = f"/api/tickets/{auto['id']}"

    assert cliente.post(
        f"{ruta}/resolver",
        json={"respuesta": "Caso cerrado."},
    ).status_code == 403

    assert cliente.post(
        f"{ruta}/confirmacion",
        json={"resuelta": True},
    ).status_code == 200

    assert cliente.post(
        f"{ruta}/confirmacion",
        json={"resuelta": False},
    ).status_code == 409

    assert consultar(cliente, auto)["estado"] == "RESUELTO"

    funcional = registrar(
        cliente,
        "No puedo adjuntar una tarea",
        "Necesito ayuda para entregar mi actividad.",
    )

    assert cliente.post(
        f"/api/tickets/{funcional['id']}/confirmacion",
        json={"resuelta": True},
    ).status_code == 409

    assert cliente.post(
        f"/api/tickets/{funcional['id']}/resolver",
        json={"respuesta": "   "},
    ).status_code == 422

    assert cliente.post(
        "/api/tickets/999999/resolver",
        json={"respuesta": "Caso cerrado."},
    ).status_code == 404

    assert consultar(cliente, funcional)["estado"] == "EN_ATENCION"
