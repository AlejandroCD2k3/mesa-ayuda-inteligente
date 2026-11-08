from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import inspect
from sqlmodel import Session, create_engine

from .models import Ticket


DB_PATH = Path(__file__).resolve().parent.parent / "mesa_ayuda.db"

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    Ticket.metadata.create_all(engine)

    columnas = {
        columna["name"]
        for columna in inspect(engine).get_columns("tickets")
    }

    if "respuesta_atencion" not in columnas:
        with engine.begin() as conexion:
            conexion.exec_driver_sql(
                "ALTER TABLE tickets ADD COLUMN respuesta_atencion VARCHAR"
            )


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
