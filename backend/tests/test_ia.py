import io
import json

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app import ia
from app.main import preparar_ticket
from app.models import (
    ArticuloConocimiento,
    CategoriaTicket,
    EstadoTicket,
    Ticket,
)


def sesion_con_articulo():
    motor = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(motor)
    sesion = Session(motor)

    sesion.add(ArticuloConocimiento(
        titulo="Consultar actividades en MAIA",
        contenido="Entra al curso y abre la sección Actividades.",
        categoria=CategoriaTicket.AUTO,
        publicado=True,
        creado_por="soporte.funcional",
    ))

    sesion.add(ArticuloConocimiento(
        titulo="Borrador secreto",
        contenido="Este contenido no debe enviarse.",
        categoria=CategoriaTicket.FUNCIONAL,
        publicado=False,
        creado_por="soporte.funcional",
    ))

    sesion.commit()
    return motor, sesion


def ticket():
    return Ticket(
        origen_sistema="MAIA",
        solicitante="estudiante.demo",
        asunto="Dónde encuentro mis actividades",
        descripcion="Quiero consultar mis actividades en MAIA",
    )


def simular_respuesta(monkeypatch, valor, capturas):
    def respuesta(peticion, timeout):
        capturas.append({
            "url": peticion.full_url,
            "auth": peticion.get_header("Authorization"),
            "solicitud": json.loads(peticion.data),
            "timeout": timeout,
        })

        envoltura = {
            "choices": [{
                "message": {
                    "content": json.dumps(
                        valor, ensure_ascii=False
                    )
                }
            }]
        }

        return io.BytesIO(
            json.dumps(envoltura).encode("utf-8")
        )

    monkeypatch.setattr(ia, "urlopen", respuesta)


def test_sin_clave_conserva_clasificador_actual(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    motor, sesion = sesion_con_articulo()

    try:
        caso = ticket()
        preparar_ticket(caso, sesion)

        assert caso.categoria == CategoriaTicket.AUTO
        assert caso.estado == EstadoTicket.PENDIENTE_CONFIRMACION
    finally:
        sesion.close()
        motor.dispose()


def test_modelo_configurable_y_conocimiento_publicado(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("LLM_MODEL", "modelo-gratis-ejemplo")
    monkeypatch.setenv("LLM_BASE_URL", "https://ejemplo.test/v1")

    capturas = []

    simular_respuesta(monkeypatch, {
        "categoria": "AUTO",
        "motivo": "Existe una solución publicada.",
        "respuesta_sugerida": "Entra al curso y abre Actividades.",
    }, capturas)

    motor, sesion = sesion_con_articulo()

    try:
        caso = ticket()
        preparar_ticket(caso, sesion)

        assert caso.estado == EstadoTicket.PENDIENTE_CONFIRMACION
        assert caso.respuesta_sugerida == (
            "Entra al curso y abre Actividades."
        )

        assert capturas[0]["url"] == (
            "https://ejemplo.test/v1/chat/completions"
        )
        assert capturas[0]["auth"] == "Bearer clave-de-prueba"

        solicitud = capturas[0]["solicitud"]

        assert solicitud["model"] == "modelo-gratis-ejemplo"

        enviado = json.loads(
            solicitud["messages"][1]["content"]
        )

        assert len(enviado["articulos_publicados"]) == 1
        assert "Borrador secreto" not in str(enviado)
        assert "estudiante.demo" not in str(enviado)
    finally:
        sesion.close()
        motor.dispose()


def test_ia_deriva_fallo_tecnico_a_soporte(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")

    simular_respuesta(monkeypatch, {
        "categoria": "TÉCNICO",
        "motivo": "Fallo de infraestructura.",
        "respuesta_sugerida": "Esta sugerencia se debe ignorar.",
    }, [])

    motor, sesion = sesion_con_articulo()

    try:
        caso = ticket()
        preparar_ticket(caso, sesion)

        assert caso.categoria == CategoriaTicket.TECNICO
        assert caso.estado == EstadoTicket.EN_ATENCION
        assert caso.responsable == "soporte_tecnico"
        assert caso.respuesta_sugerida is None
    finally:
        sesion.close()
        motor.dispose()


def test_respuesta_invalida_usa_fallback(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")

    simular_respuesta(monkeypatch, {
        "categoria": "NO_EXISTE"
    }, [])

    motor, sesion = sesion_con_articulo()

    try:
        caso = ticket()
        preparar_ticket(caso, sesion)

        assert caso.categoria == CategoriaTicket.AUTO
        assert caso.estado == EstadoTicket.PENDIENTE_CONFIRMACION
    finally:
        sesion.close()
        motor.dispose()


def test_sin_articulos_no_consume_cuota(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")

    motor, sesion = sesion_con_articulo()

    try:
        for articulo in sesion.exec(
            select(ArticuloConocimiento)
        ).all():
            articulo.publicado = False

        sesion.commit()

        def prohibido(*args, **kwargs):
            raise AssertionError("No deberia consultar la API")

        monkeypatch.setattr(ia, "urlopen", prohibido)

        caso = ticket()
        preparar_ticket(caso, sesion)

        assert caso.categoria == CategoriaTicket.AUTO
    finally:
        sesion.close()
        motor.dispose()


def test_error_de_cuota_usa_fallback(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")

    motor, sesion = sesion_con_articulo()

    try:
        def cuota(*args, **kwargs):
            raise OSError("429 rate limit")

        monkeypatch.setattr(ia, "urlopen", cuota)

        caso = ticket()
        preparar_ticket(caso, sesion)

        assert caso.categoria == CategoriaTicket.AUTO
        assert caso.respuesta_sugerida
    finally:
        sesion.close()
        motor.dispose()



def test_edicion_no_repite_llamadas_llm(monkeypatch):
    from fastapi.testclient import TestClient
    from app import database, main
    from app.api import tickets as api_tickets

    motor = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    monkeypatch.setattr(database, "engine", motor)
    monkeypatch.setenv("LLM_API_KEY", "clave-simulada")

    llamadas = []

    def ia_simulada(sesion, caso):
        llamadas.append(caso.asunto)
        return (
            CategoriaTicket.TECNICO,
            "Requiere soporte tecnico.",
            None,
        )

    monkeypatch.setattr(
        api_tickets,
        "analizar_ticket_con_ia",
        ia_simulada,
    )

    try:
        with TestClient(main.app) as cliente:
            acceso = cliente.post(
                "/api/demo/sesion",
                json={"usuario_id": "estudiante.demo"},
            )

            assert acceso.status_code == 200, acceso.text

            headers = {
                "Authorization": (
                    f"Bearer {acceso.json()['token']}"
                )
            }

            creacion = cliente.post(
                "/api/tickets",
                headers=headers,
                json={
                    "origen_sistema": "MAIA",
                    "solicitante": "estudiante.demo",
                    "asunto": "Error ficticio de servidor",
                    "descripcion": (
                        "El servicio de pruebas no responde."
                    ),
                },
            )

            assert creacion.status_code == 201, creacion.text
            assert len(llamadas) == 1
            assert creacion.json()["estado"] == "EN_ATENCION"

            id_creado = creacion.json()["id"]

            edicion = cliente.patch(
                f"/api/tickets/{id_creado}",
                headers=headers,
                json={
                    "descripcion": "El error ficticio persiste."
                },
            )
            assert edicion.status_code == 200, edicion.text

            # Una llamada al crear, ninguna adicional al editar.
            assert len(llamadas) == 1

    finally:
        motor.dispose()
