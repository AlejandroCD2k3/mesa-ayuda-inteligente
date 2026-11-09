import unicodedata

from .tipos import CategoriaTicket


def clasificar_ticket(
    origen_sistema: str,
    asunto: str,
    descripcion: str,
) -> tuple[CategoriaTicket, str]:
    texto = " ".join((origen_sistema, asunto, descripcion)).casefold()
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )

    fallos_tecnicos = (
        "http 500", "error 500",
        "http 502", "error 502",
        "http 503", "error 503",
        "error de servidor", "servidor caido",
        "error de integracion", "fallo de integracion",
        "error de api", "falla en la api",
        "timeout", "traceback",
    )

    if any(indicio in texto for indicio in fallos_tecnicos):
        return (
            CategoriaTicket.TECNICO,
            "La solicitud describe un fallo tecnico de servidor, API o integracion.",
        )

    if any(
        indicio in texto
        for indicio in ("adjuntar tarea", "adjuntar una tarea",
                        "subir tarea", "entregar tarea")
    ):
        return (
            CategoriaTicket.FUNCIONAL,
            "La solicitud requiere asistencia funcional para entregar una tarea.",
        )

    consulta_actividades = (
        "maia" in texto
        and "actividad" in texto
        and any(
            indicio in texto
            for indicio in ("donde", "como ver", "como consult",
                            "consultar", "encontrar")
        )
    )

    reporta_fallo = any(
        indicio in texto
        for indicio in ("no puedo", "no me deja", "error", "problema", "falla")
    )

    if consulta_actividades and not reporta_fallo:
        return (
            CategoriaTicket.AUTO,
            "Consulta frecuente sobre como encontrar actividades en MAIA.",
        )

    return (
        CategoriaTicket.FUNCIONAL,
        "No se identifico una consulta frecuente resuelta ni un fallo tecnico "
        "concreto; requiere revision funcional.",
    )
