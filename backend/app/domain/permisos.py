"""Reglas puras de acceso del prototipo de demostración."""
from .tipos import CategoriaTicket

LEGADOS = ("usuario.demo", "estudiante.pruebas")


def solicitantes_visibles(usuario_id: str) -> tuple[str, ...]:
    return (usuario_id,) + (LEGADOS if usuario_id == "estudiante.demo" else ())


def puede_ver(rol: str, usuario_id: str, solicitante: str, responsable: str | None) -> bool:
    if rol == "estudiante":
        return solicitante in solicitantes_visibles(usuario_id)
    return responsable == rol


def categorias_editables(rol: str) -> tuple[CategoriaTicket, ...]:
    if rol == "soporte_funcional":
        return (CategoriaTicket.AUTO, CategoriaTicket.FUNCIONAL)
    if rol == "soporte_tecnico":
        return (CategoriaTicket.TECNICO,)
    return ()
