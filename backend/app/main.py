"""Punto de entrada: composición de adaptadores y arranque."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.conocimiento import router as router_conocimiento
from .api.tickets import router as router_tickets, preparar_ticket, registrar_evento
from .database import init_db
from .sesiones_demo import router as router_demo


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Mesa de Ayuda Inteligente", lifespan=lifespan)
app.include_router(router_demo)
app.include_router(router_conocimiento)
app.include_router(router_tickets)


@app.get("/api/health", include_in_schema=False)
@app.get("/health")
def health():
    return {"status": "ok"}
