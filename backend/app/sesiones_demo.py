"""Perfiles y sesiones temporales para demostracion local, no autenticacion real."""

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel


@dataclass(frozen=True)
class UsuarioDemo:
    id: str
    nombre: str
    rol: str


USUARIOS_DEMO = {
    "estudiante.demo": UsuarioDemo(
        "estudiante.demo", "Estudiante demo", "estudiante"
    ),
    "estudiante.alterno": UsuarioDemo(
        "estudiante.alterno", "Estudiante alterno", "estudiante"
    ),
    "soporte.funcional": UsuarioDemo(
        "soporte.funcional", "Soporte funcional", "soporte_funcional"
    ),
    "soporte.tecnico": UsuarioDemo(
        "soporte.tecnico", "Soporte tecnico", "soporte_tecnico"
    ),
}

_CLAVE_TEMPORAL = secrets.token_bytes(32)
_DURACION_SEGUNDOS = 8 * 60 * 60


class SeleccionDemo(BaseModel):
    usuario_id: Literal[
        "estudiante.demo",
        "estudiante.alterno",
        "soporte.funcional",
        "soporte.tecnico",
    ]


router = APIRouter(prefix="/api/demo", tags=["Demo local"])


@router.get("/usuarios")
def listar_usuarios_demo() -> list[UsuarioDemo]:
    return list(USUARIOS_DEMO.values())


@router.post("/sesion")
def iniciar_sesion_demo(datos: SeleccionDemo) -> dict:
    usuario = USUARIOS_DEMO[datos.usuario_id]
    expiracion = int(time.time()) + _DURACION_SEGUNDOS

    carga = f"{usuario.id}.{expiracion}"
    firma = hmac.new(
        _CLAVE_TEMPORAL,
        carga.encode(),
        hashlib.sha256,
    ).hexdigest()

    return {
        "token": f"{carga}.{firma}",
        "usuario": usuario,
    }


def obtener_usuario_demo(
    authorization: str | None = Header(default=None),
) -> UsuarioDemo:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Selecciona un perfil de demostracion.",
        )

    try:
        identificador, expiracion_texto, firma = (
            authorization[7:].rsplit(".", 2)
        )

        usuario = USUARIOS_DEMO.get(identificador)
        expiracion = int(expiracion_texto)

        mensaje = f"{identificador}.{expiracion_texto}"

        esperada = hmac.new(
            _CLAVE_TEMPORAL,
            mensaje.encode(),
            hashlib.sha256,
        ).hexdigest()

        if (
            usuario is None
            or expiracion <= time.time()
            or not hmac.compare_digest(firma, esperada)
        ):
            raise ValueError("Sesion invalida")

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Sesion de demostracion invalida o vencida.",
        ) from None

    return usuario


@router.get("/yo")
def perfil_actual(
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
) -> UsuarioDemo:
    return usuario
