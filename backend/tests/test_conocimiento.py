from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select

from app import database
from app.main import app
from app.models import ArticuloConocimiento, Ticket


@pytest.fixture
def cliente(tmp_path: Path, monkeypatch):
    motor = create_engine(
        f"sqlite:///{(tmp_path / 'conocimiento.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", motor)

    try:
        with TestClient(app) as c:
            yield c
    finally:
        motor.dispose()


def acceso(cliente, identificador):
    respuesta = cliente.post(
        "/api/demo/sesion",
        json={"usuario_id": identificador},
    )

    assert respuesta.status_code == 200
    return {
        "Authorization": f"Bearer {respuesta.json()['token']}"
    }


def nuevo(
    cliente,
    headers,
    categoria="FUNCIONAL",
    publicado=True,
    titulo="Acceso a MAIA",
):
    return cliente.post(
        "/api/conocimiento",
        headers=headers,
        json={
            "titulo": titulo,
            "contenido": (
                "Comprueba la contraseña y vuelve "
                "a iniciar sesión."
            ),
            "categoria": categoria,
            "publicado": publicado,
        },
    )


def test_consultas_requieren_sesion(cliente):
    assert cliente.get("/api/conocimiento").status_code == 401
    assert cliente.get("/api/conocimiento/1").status_code == 401
    assert nuevo(cliente, {}).status_code == 401


def test_soporte_crea_y_estudiante_consulta(cliente):
    soporte = acceso(cliente, "soporte.funcional")
    estudiante = acceso(cliente, "estudiante.demo")

    respuesta = nuevo(cliente, soporte)
    assert respuesta.status_code == 201

    articulo = respuesta.json()

    assert articulo["creado_por"] == "soporte.funcional"
    assert articulo["categoria"] == "FUNCIONAL"

    listado = cliente.get(
        "/api/conocimiento",
        headers=estudiante,
    ).json()

    assert listado[0]["id"] == articulo["id"]

    detalle = cliente.get(
        f"/api/conocimiento/{articulo['id']}",
        headers=estudiante,
    )

    assert detalle.status_code == 200


def test_estudiante_no_publica_y_equipos_respetan_categoria(cliente):
    estudiante = acceso(cliente, "estudiante.demo")
    funcional = acceso(cliente, "soporte.funcional")
    tecnico = acceso(cliente, "soporte.tecnico")

    assert nuevo(cliente, estudiante).status_code == 403
    assert nuevo(
        cliente, tecnico, categoria="FUNCIONAL"
    ).status_code == 403
    assert nuevo(
        cliente, funcional, categoria="TÉCNICO"
    ).status_code == 403

    articulo = nuevo(
        cliente, tecnico, categoria="TÉCNICO"
    ).json()

    assert articulo["creado_por"] == "soporte.tecnico"

    edicion = cliente.put(
        f"/api/conocimiento/{articulo['id']}",
        headers=funcional,
        json={
            "titulo": "Nuevo titulo",
            "contenido": "Respuesta editada",
            "publicado": True,
        },
    )

    assert edicion.status_code == 403


def test_borradores_no_visibles_a_otros_perfiles(cliente):
    funcional = acceso(cliente, "soporte.funcional")
    tecnico = acceso(cliente, "soporte.tecnico")
    estudiante = acceso(cliente, "estudiante.demo")

    borrador = nuevo(
        cliente, funcional, publicado=False
    ).json()

    ruta = f"/api/conocimiento/{borrador['id']}"

    assert cliente.get(
        ruta, headers=estudiante
    ).status_code == 404

    assert cliente.get(
        ruta, headers=tecnico
    ).status_code == 404

    assert cliente.get(
        ruta, headers=funcional
    ).status_code == 200

    assert cliente.get(
        "/api/conocimiento", headers=estudiante
    ).json() == []

    assert len(cliente.get(
        "/api/conocimiento", headers=funcional
    ).json()) == 1


def test_edicion_publicacion_y_busqueda(cliente):
    soporte = acceso(cliente, "soporte.funcional")
    estudiante = acceso(cliente, "estudiante.alterno")

    articulo = nuevo(
        cliente, soporte, publicado=False
    ).json()

    ruta = f"/api/conocimiento/{articulo['id']}"

    actualizacion = cliente.put(
        ruta,
        headers=soporte,
        json={
            "titulo": "Recuperar contraseña",
            "contenido": (
                "Abre el formulario de recuperación "
                "de acceso."
            ),
            "publicado": True,
        },
    )

    assert actualizacion.status_code == 200
    assert actualizacion.json()["publicado"] is True

    busqueda = cliente.get(
        "/api/conocimiento",
        params={"q": "CONTRASEÑA"},
        headers=estudiante,
    )

    assert len(busqueda.json()) == 1

    sin_resultados = cliente.get(
        "/api/conocimiento",
        params={"q": "impresora"},
        headers=estudiante,
    )

    assert sin_resultados.json() == []

    assert cliente.put(
        ruta,
        headers=estudiante,
        json={
            "titulo": "Incorrecto",
            "contenido": "Incorrecto",
            "publicado": False,
        },
    ).status_code == 403


def test_creacion_tabla_conserva_tickets_existentes(cliente):
    with Session(database.engine) as sesion:
        sesion.add(Ticket(
            origen_sistema="MAIA",
            solicitante="usuario.demo",
            asunto="Ticket previo",
            descripcion="Solicitud preexistente",
        ))
        sesion.commit()

    database.init_db()

    with Session(database.engine) as sesion:
        assert sesion.get(Ticket, 1).asunto == "Ticket previo"
        assert sesion.exec(
            select(ArticuloConocimiento)
        ).all() == []
