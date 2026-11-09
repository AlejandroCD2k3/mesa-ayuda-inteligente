"""Carga reproducible de datos ficticios para la evaluación."""

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, select

from app.database import DB_PATH, engine, init_db
from app.models import (
    ArticuloConocimiento,
    CategoriaTicket,
    EstadoTicket,
    Ticket,
    TicketEvento,
)

CATALOGO = Path(__file__).resolve().parents[1] / "datos_demo.json"


def respaldar():
    if not DB_PATH.exists():
        return

    raiz = (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        / "MesaAyuda"
        / "respaldos"
    )
    raiz.mkdir(parents=True, exist_ok=True)

    destino = raiz / (
        f"mesa_ayuda_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    )

    with sqlite3.connect(str(DB_PATH)) as origen:
        with sqlite3.connect(str(destino)) as copia:
            origen.backup(copia)

    print("RESPALDO:", destino)


def preparar(reset):
    datos = json.loads(CATALOGO.read_text(encoding="utf-8"))

    articulos = datos["articulos"]
    tickets = datos["tickets"]

    titulos = [item["titulo"] for item in articulos]

    if len(titulos) != len(set(titulos)):
        raise ValueError("Hay artículos con títulos repetidos.")

    contenido_por_titulo = {
        item["titulo"]: item["contenido"]
        for item in articulos
    }

    # Validar el catálogo completo antes de modificar SQLite.
    for item in articulos:
        CategoriaTicket(item["categoria"])
        if not item["titulo"].strip() or not item["contenido"].strip():
            raise ValueError("Artículo incompleto.")

    for item in tickets:
        CategoriaTicket(item["categoria"])
        EstadoTicket(item["estado"])
        if item.get("articulo_respuesta"):
            if item["articulo_respuesta"] not in contenido_por_titulo:
                raise ValueError("Artículo de respuesta inexistente.")

    if reset:
        respaldar()

    init_db()
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        existentes = any(
            session.exec(select(model.id).limit(1)).first() is not None
            for model in (
                ArticuloConocimiento,
                Ticket,
                TicketEvento,
            )
        )

        if existentes and not reset:
            print(
                "La base ya tiene datos. "
                "Se conservaron sin cambios."
            )
            return

        try:
            if reset:
                session.exec(delete(TicketEvento))
                session.exec(delete(Ticket))
                session.exec(delete(ArticuloConocimiento))

                print(
                    "LIMPIEZA: artículos, tickets e historial "
                    "anteriores eliminados."
                )

            for indice, item in enumerate(articulos, 1):
                categoria = CategoriaTicket(item["categoria"])

                autor = (
                    "soporte.tecnico"
                    if categoria == CategoriaTicket.TECNICO
                    else "soporte.funcional"
                )

                session.add(ArticuloConocimiento(
                    titulo=item["titulo"],
                    contenido=item["contenido"],
                    categoria=categoria,
                    publicado=True,
                    creado_por=autor,
                ))

                print(
                    f"ARTÍCULO {indice}/{len(articulos)}: "
                    f"{item['titulo']}"
                )

            for indice, item in enumerate(tickets, 1):
                respuesta = None

                if item.get("articulo_respuesta"):
                    respuesta = contenido_por_titulo[
                        item["articulo_respuesta"]
                    ]

                caso = Ticket(
                    origen_sistema=item["origen_sistema"],
                    solicitante=item["solicitante"],
                    asunto=item["asunto"],
                    descripcion=item["descripcion"],
                    categoria=CategoriaTicket(item["categoria"]),
                    estado=EstadoTicket(item["estado"]),
                    responsable=item.get("responsable"),
                    motivo_clasificacion=item["motivo_clasificacion"],
                    respuesta_sugerida=respuesta,
                    respuesta_atencion=item.get("respuesta_atencion"),
                )

                session.add(caso)
                session.flush()

                session.add(TicketEvento(
                    ticket_id=caso.id,
                    tipo="CREACION",
                    detalle="Solicitud ficticia registrada.",
                    actor=caso.solicitante,
                ))

                session.add(TicketEvento(
                    ticket_id=caso.id,
                    tipo="CLASIFICACION",
                    detalle=(
                        f"Clasificado como {caso.categoria.value}."
                    ),
                    actor="sistema",
                ))

                if caso.responsable:
                    session.add(TicketEvento(
                        ticket_id=caso.id,
                        tipo="ASIGNACION",
                        detalle=f"Asignado a {caso.responsable}.",
                        actor="sistema",
                    ))

                if caso.estado == EstadoTicket.RESUELTO:
                    session.add(TicketEvento(
                        ticket_id=caso.id,
                        tipo="RESPUESTA",
                        detalle="Se registró una respuesta de soporte.",
                        actor="soporte.funcional",
                    ))

                    session.add(TicketEvento(
                        ticket_id=caso.id,
                        tipo="CIERRE",
                        detalle="El caso quedó resuelto.",
                        actor=caso.solicitante,
                    ))

                print(
                    f"TICKET {indice}/{len(tickets)}: "
                    f"{caso.asunto}"
                )

            session.commit()

        except Exception:
            session.rollback()
            raise

    print(
        f"LISTO: {len(articulos)} artículos y "
        f"{len(tickets)} tickets ficticios."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    opciones = parser.add_mutually_exclusive_group(required=True)

    opciones.add_argument(
        "--reset",
        action="store_true",
        help="Respaldar, limpiar y cargar datos ficticios",
    )
    opciones.add_argument(
        "--init",
        action="store_true",
        help="Cargar únicamente si la base está vacía",
    )

    argumentos = parser.parse_args()
    preparar(reset=argumentos.reset)
