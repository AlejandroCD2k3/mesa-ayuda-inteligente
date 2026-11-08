from .models import CategoriaTicket


def sugerir_solucion(categoria: CategoriaTicket) -> str | None:
    if categoria != CategoriaTicket.AUTO:
        return None

    return (
        "Ingresa a MAIA, abre el curso correspondiente y revisa las "
        "actividades publicadas. Si no encuentras la actividad que buscas, "
        "indica que esta sugerencia no resolvio tu consulta para recibir "
        "apoyo funcional."
    )
