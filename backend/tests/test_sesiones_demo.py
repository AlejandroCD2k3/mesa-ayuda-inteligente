from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from app import database, sesiones_demo
from app.main import app


@pytest.fixture
def cliente_demo(tmp_path: Path, monkeypatch):
    motor = create_engine(
        f"sqlite:///{(tmp_path / 'sesion-demo.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )

    monkeypatch.setattr(database, "engine", motor)

    try:
        with TestClient(app) as cliente:
            yield cliente
    finally:
        motor.dispose()


def test_catalogo_demo(cliente_demo):
    respuesta = cliente_demo.get("/api/demo/usuarios")

    assert respuesta.status_code == 200
    assert {u["id"] for u in respuesta.json()} == set(
        sesiones_demo.USUARIOS_DEMO
    )


def test_sesion_para_cada_perfil(cliente_demo):
    for usuario_id, usuario in sesiones_demo.USUARIOS_DEMO.items():
        respuesta = cliente_demo.post(
            "/api/demo/sesion",
            json={"usuario_id": usuario_id},
        )

        assert respuesta.status_code == 200

        token = respuesta.json()["token"]

        assert respuesta.json()["usuario"]["rol"] == usuario.rol

        perfil = cliente_demo.get(
            "/api/demo/yo",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert perfil.status_code == 200
        assert perfil.json()["id"] == usuario_id


def test_identidad_desconocida_rechazada(cliente_demo):
    respuesta = cliente_demo.post(
        "/api/demo/sesion",
        json={"usuario_id": "inventado"},
    )

    assert respuesta.status_code == 422


def test_no_se_acepta_sesion_ausente(cliente_demo):
    respuesta = cliente_demo.get("/api/demo/yo")

    assert respuesta.status_code == 401


def test_no_se_acepta_token_modificado(cliente_demo):
    token = cliente_demo.post(
        "/api/demo/sesion",
        json={"usuario_id": "estudiante.demo"},
    ).json()["token"]

    respuesta = cliente_demo.get(
        "/api/demo/yo",
        headers={"Authorization": f"Bearer {token}x"},
    )

    assert respuesta.status_code == 401


def test_sesion_vencida_rechazada(cliente_demo, monkeypatch):
    token = cliente_demo.post(
        "/api/demo/sesion",
        json={"usuario_id": "estudiante.demo"},
    ).json()["token"]

    ahora = sesiones_demo.time.time()

    monkeypatch.setattr(
        sesiones_demo.time,
        "time",
        lambda: ahora + 9 * 60 * 60,
    )

    respuesta = cliente_demo.get(
        "/api/demo/yo",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert respuesta.status_code == 401
