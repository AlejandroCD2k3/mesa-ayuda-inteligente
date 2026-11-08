import pytest

from app.clasificacion import clasificar_ticket
from app.models import CategoriaTicket


@pytest.mark.parametrize(
    ("sistema", "asunto", "descripcion", "esperada"),
    [
        (
            "MAIA",
            "¿Dónde encuentro mis actividades?",
            "Quiero consultar las actividades del curso.",
            CategoriaTicket.AUTO,
        ),
        (
            "MAIA",
            "No puedo adjuntar una tarea",
            "Necesito apoyo para entregar la actividad.",
            CategoriaTicket.FUNCIONAL,
        ),
        (
            "EvaluIA",
            "Error HTTP 500",
            "Falla al conectar EvaluIA con Moodle.",
            CategoriaTicket.TECNICO,
        ),
        (
            "MAIA",
            "Consulta sobre permisos",
            "Necesito que revisen mi situación.",
            CategoriaTicket.FUNCIONAL,
        ),
    ],
)
def test_clasificacion(sistema, asunto, descripcion, esperada):
    categoria, motivo = clasificar_ticket(sistema, asunto, descripcion)

    assert categoria == esperada
    assert motivo.strip()
