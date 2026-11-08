from pathlib import Path

from sqlalchemy import inspect
from sqlmodel import create_engine

from app import database


def test_base_anterior_conserva_tickets(tmp_path: Path, monkeypatch):
    ruta = tmp_path / "anterior.db"
    motor = create_engine(f"sqlite:///{ruta.as_posix()}")

    with motor.begin() as conexion:
        conexion.exec_driver_sql(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY,
                origen_sistema VARCHAR NOT NULL,
                solicitante VARCHAR NOT NULL,
                asunto VARCHAR NOT NULL,
                descripcion VARCHAR NOT NULL,
                categoria VARCHAR,
                estado VARCHAR NOT NULL,
                responsable VARCHAR,
                motivo_clasificacion VARCHAR,
                respuesta_sugerida VARCHAR,
                fecha_creacion DATETIME NOT NULL,
                fecha_actualizacion DATETIME NOT NULL
            )
            """
        )

        conexion.exec_driver_sql(
            """
            INSERT INTO tickets (
                id, origen_sistema, solicitante, asunto, descripcion,
                estado, fecha_creacion, fecha_actualizacion
            ) VALUES (
                1, 'MAIA', 'usuario.demo', 'Solicitud existente',
                'Descripcion original', 'ABIERTO',
                '2026-11-07 12:00:00', '2026-11-07 12:00:00'
            )
            """
        )

    monkeypatch.setattr(database, "engine", motor)

    database.init_db()
    database.init_db()

    columnas = {
        columna["name"]
        for columna in inspect(motor).get_columns("tickets")
    }

    assert "respuesta_atencion" in columnas

    with motor.connect() as conexion:
        fila = conexion.exec_driver_sql(
            "SELECT asunto, respuesta_atencion FROM tickets WHERE id = 1"
        ).one()

    assert fila[0] == "Solicitud existente"
    assert fila[1] is None

    motor.dispose()
