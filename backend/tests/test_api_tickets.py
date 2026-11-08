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
            sesion = test_client.post(
                "/api/demo/sesion",
                json={"usuario_id": "estudiante.demo"},
            ).json()
            test_client.headers.update({
                "Authorization": f"Bearer {sesion['token']}"
            })
            yield test_client
    finally:
        motor_prueba.dispose()


def cabeceras_soporte(cliente, tecnico=False):
    identidad = (
        "soporte.tecnico" if tecnico else "soporte.funcional"
    )
    sesion = cliente.post(
        "/api/demo/sesion",
        json={"usuario_id": identidad},
    ).json()
    return {"Authorization": f"Bearer {sesion['token']}"}


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
    assert ticket["estado"] == "EN_ATENCION"
    assert ticket["responsable"] == "soporte_funcional"
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
    assert respuesta.json()["estado"] == "EN_ATENCION"

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
    assert ticket["respuesta_sugerida"]
    assert ticket["estado"] == "PENDIENTE_CONFIRMACION"


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

def datos_auto():
    return {
        "origen_sistema": "MAIA",
        "solicitante": "usuario.demo",
        "asunto": "¿Dónde encuentro mis actividades?",
        "descripcion": "Quiero consultar las actividades del curso.",
    }


def test_auto_recibe_sugerencia_y_espera_confirmacion(cliente):
    respuesta = cliente.post("/api/tickets", json=datos_auto())

    assert respuesta.status_code == 201
    ticket = respuesta.json()

    assert ticket["categoria"] == "AUTO"
    assert ticket["estado"] == "PENDIENTE_CONFIRMACION"
    assert ticket["respuesta_sugerida"]
    assert ticket["responsable"] is None


def test_aceptar_solucion_resuelve_ticket(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/confirmacion",
        json={"resuelta": True},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RESUELTO"
    assert respuesta.json()["categoria"] == "AUTO"

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["estado"] == "RESUELTO"


def test_rechazar_solucion_escala_a_funcional(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/confirmacion",
        json={"resuelta": False},
    )

    assert respuesta.status_code == 200

    actualizado = respuesta.json()

    assert actualizado["categoria"] == "FUNCIONAL"
    assert actualizado["estado"] == "EN_ATENCION"
    assert actualizado["responsable"] == "soporte_funcional"
    assert actualizado["motivo_clasificacion"]
    assert actualizado["respuesta_sugerida"]

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["estado"] == "EN_ATENCION"
    assert guardado["responsable"] == "soporte_funcional"


def test_no_confirmar_ticket_funcional(cliente):
    ticket = cliente.post("/api/tickets", json=datos_ticket()).json()

    assert ticket["categoria"] == "FUNCIONAL"
    assert ticket["respuesta_sugerida"] is None

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/confirmacion",
        json={"resuelta": True},
    )

    assert respuesta.status_code == 409


def test_confirmacion_ticket_inexistente(cliente):
    respuesta = cliente.post(
        "/api/tickets/999/confirmacion",
        json={"resuelta": True},
    )

    assert respuesta.status_code == 404


def test_no_confirmar_dos_veces(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()
    ruta = f"/api/tickets/{ticket['id']}/confirmacion"

    primera = cliente.post(ruta, json={"resuelta": True})
    segunda = cliente.post(ruta, json={"resuelta": False})

    assert primera.status_code == 200
    assert segunda.status_code == 409

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["estado"] == "RESUELTO"


def test_confirmacion_rechaza_datos_invalidos(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()
    ruta = f"/api/tickets/{ticket['id']}/confirmacion"

    for datos in (
        {},
        {"resuelta": None},
        {"resuelta": "si"},
        {"resuelta": True, "estado": "RESUELTO"},
    ):
        assert cliente.post(ruta, json=datos).status_code == 422

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["estado"] == "PENDIENTE_CONFIRMACION"


def test_no_editar_ticket_pendiente_ni_resuelto(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()
    ruta = f"/api/tickets/{ticket['id']}"

    assert cliente.patch(
        ruta, json={"asunto": "Otro asunto"}
    ).status_code == 409

    cliente.post(
        f"{ruta}/confirmacion",
        json={"resuelta": True},
    )

    assert cliente.patch(
        ruta, json={"asunto": "Otro asunto"}
    ).status_code == 409

    guardado = cliente.get(ruta).json()
    assert guardado["asunto"] == ticket["asunto"]


def test_reclasificacion_a_auto_genera_sugerencia(cliente):
    datos = datos_ticket()
    creado = cliente.post("/api/tickets", json=datos).json()

    assert creado["categoria"] == "FUNCIONAL"

    respuesta = cliente.patch(
        f"/api/tickets/{creado['id']}",
        json={
            "asunto": "¿Dónde encuentro mis actividades?",
            "descripcion": "Quiero consultar las actividades del curso.",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["categoria"] == "AUTO"
    assert respuesta.json()["estado"] == "PENDIENTE_CONFIRMACION"
    assert respuesta.json()["respuesta_sugerida"]
def test_resolver_ticket_funcional(cliente):
    ticket = cliente.post("/api/tickets", json=datos_ticket()).json()

    assert ticket["categoria"] == "FUNCIONAL"
    assert ticket["estado"] == "EN_ATENCION"
    assert ticket["responsable"] == "soporte_funcional"

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        json={"respuesta": "Se revisaron los permisos del usuario."},
        headers=cabeceras_soporte(cliente),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RESUELTO"
    assert respuesta.json()["respuesta_atencion"] == (
        "Se revisaron los permisos del usuario."
    )

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["respuesta_atencion"] == respuesta.json()["respuesta_atencion"]


def test_resolver_ticket_tecnico(cliente):
    datos = datos_ticket()
    datos["origen_sistema"] = "EvaluIA"
    datos["asunto"] = "Error HTTP 500"
    datos["descripcion"] = "Error de integracion con Moodle."

    ticket = cliente.post("/api/tickets", json=datos).json()

    assert ticket["categoria"] == "TÉCNICO"
    assert ticket["estado"] == "EN_ATENCION"
    assert ticket["responsable"] == "soporte_tecnico"

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        json={"respuesta": "Se restablecio la integracion con Moodle."},
        headers=cabeceras_soporte(cliente, tecnico=True),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RESUELTO"


def test_resolver_ticket_auto_rechazado(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()
    ruta = f"/api/tickets/{ticket['id']}"

    rechazo = cliente.post(
        f"{ruta}/confirmacion",
        json={"resuelta": False},
    )

    assert rechazo.status_code == 200
    assert rechazo.json()["responsable"] == "soporte_funcional"

    cierre = cliente.post(
        f"{ruta}/resolver",
        json={"respuesta": "Se acompano al estudiante durante la consulta."},
        headers=cabeceras_soporte(cliente),
    )

    assert cierre.status_code == 200
    assert cierre.json()["estado"] == "RESUELTO"
    assert cierre.json()["categoria"] == "FUNCIONAL"
    assert cierre.json()["respuesta_sugerida"]
    assert cierre.json()["respuesta_atencion"]


def test_no_resolver_auto_pendiente(cliente):
    ticket = cliente.post("/api/tickets", json=datos_auto()).json()

    respuesta = cliente.post(
        f"/api/tickets/{ticket['id']}/resolver",
        json={"respuesta": "Atendido."},
    )

    assert respuesta.status_code == 403

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["estado"] == "PENDIENTE_CONFIRMACION"


def test_no_resolver_dos_veces(cliente):
    ticket = cliente.post("/api/tickets", json=datos_ticket()).json()
    ruta = f"/api/tickets/{ticket['id']}/resolver"

    headers = cabeceras_soporte(cliente)
    primera = cliente.post(
        ruta, json={"respuesta": "Caso atendido."}, headers=headers
    )
    segunda = cliente.post(
        ruta, json={"respuesta": "Otra respuesta."}, headers=headers
    )

    assert primera.status_code == 200
    assert segunda.status_code == 409

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["respuesta_atencion"] == "Caso atendido."


def test_resolucion_rechaza_datos_invalidos(cliente):
    ticket = cliente.post("/api/tickets", json=datos_ticket()).json()
    ruta = f"/api/tickets/{ticket['id']}/resolver"

    for datos in (
        {},
        {"respuesta": ""},
        {"respuesta": "   "},
        {"respuesta": None},
        {"respuesta": "Atendido", "estado": "RESUELTO"},
    ):
        assert cliente.post(ruta, json=datos).status_code == 422

    guardado = cliente.get(f"/api/tickets/{ticket['id']}").json()
    assert guardado["estado"] == "EN_ATENCION"


def test_resolver_ticket_inexistente(cliente):
    respuesta = cliente.post(
        "/api/tickets/999/resolver",
        json={"respuesta": "Caso atendido."},
    )

    assert respuesta.status_code == 404
