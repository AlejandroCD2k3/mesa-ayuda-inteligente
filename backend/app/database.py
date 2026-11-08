from pathlib import Path

from sqlmodel import create_engine

from .models import Ticket


DB_PATH = Path(__file__).resolve().parent.parent / "mesa_ayuda.db"

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    Ticket.metadata.create_all(engine)
