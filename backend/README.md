# Backend

API REST de la Mesa de Ayuda Inteligente UNAD IA 360.

## Requisitos

- Python 3.12
- uv

## Instalación

Desde el directorio `backend`:

    uv sync

## Desarrollo

    uv run uvicorn app.main:app --reload

API: http://127.0.0.1:8000

Documentación OpenAPI: http://127.0.0.1:8000/docs

## Pruebas

    uv run python -m pytest -q

## Endpoints

- GET /health: estado del servicio.

## Dependencias

Las dependencias se gestionan en `pyproject.toml`.
Las versiones resueltas se conservan en `uv.lock`.

## Modelo de tickets

Los tickets se almacenan mediante SQLModel en SQLite.

El modelo `Ticket` incluye los datos de la solicitud,
su categoria, estado, responsable y fechas de seguimiento.

La base local se guarda en `backend/mesa_ayuda.db`
y no se incluye en Git.

Para inicializar la tabla, desde `backend`:

    uv run python -c "from app.database import init_db; init_db()"

Para ejecutar todas las pruebas:

    uv run python -m pytest -q

Las pruebas de persistencia utilizan bases temporales.

## API REST de tickets

La API permite registrar, consultar y editar solicitudes.

Endpoints disponibles:

- `POST /api/tickets`: registrar una solicitud.
- `GET /api/tickets`: listar solicitudes.
- `GET /api/tickets/{id}`: consultar una solicitud.
- `PATCH /api/tickets/{id}`: actualizar asunto o descripcion.

Los tickets nuevos comienzan abiertos y sin clasificar.
Los cambios de categoria, estado y responsable se implementaran
en las siguientes etapas del flujo de atencion.

La base SQLite se inicializa al arrancar FastAPI.

Para ejecutar el servidor desde `backend`:

    uv run uvicorn app.main:app --reload

Documentacion interactiva: http://127.0.0.1:8000/docs

## Clasificacion de tickets

Al registrar un ticket, la API asigna una categoria:

- `AUTO`: consulta frecuente que puede recibir una solucion sugerida.
- `FUNCIONAL`: solicitud que necesita atencion funcional.
- `TÉCNICO`: fallo de servidor, API o integracion identificado.

Cada clasificacion incluye un motivo que se guarda con el ticket.

Si se modifica el asunto o la descripcion, la API vuelve a clasificar
la solicitud.

La version actual utiliza reglas sencillas para los escenarios del
prototipo. No es un clasificador de lenguaje general.

La clasificacion no resuelve el ticket ni asigna un responsable.
Estas acciones se implementaran en las siguientes etapas.

## Sugerencias y confirmacion

Cuando una solicitud se clasifica como `AUTO`, la API
asocia una respuesta sugerida y establece el estado
`PENDIENTE_CONFIRMACION`.

El solicitante puede responder mediante:

    POST /api/tickets/{ticket_id}/confirmacion

Ejemplo de solicitud:

    {"resuelta": true}

Si confirma que la sugerencia funciono, el ticket queda
`RESUELTO`.

Si responde `false`, pasa a `FUNCIONAL`, con estado
`EN_ATENCION` y responsable `soporte_funcional`.

Las confirmaciones repetidas y las operaciones incompatibles
con el estado actual se rechazan con HTTP 409.

La sugerencia disponible cubre el caso de consulta de
actividades en MAIA. No representa una solucion general
para cualquier solicitud.

La API utiliza identidades de demostracion; todavia no
autentica al solicitante que confirma la solucion.

## Atencion funcional y tecnica

Los tickets que no reciben una solucion automatica
se asignan al equipo correspondiente:

- `FUNCIONAL`: responsable `soporte_funcional`.
- `TÉCNICO`: responsable `soporte_tecnico`.

Ambos comienzan en estado `EN_ATENCION`.

Los tickets `AUTO` cuya sugerencia es rechazada tambien
pasan a atencion funcional.

### Registrar una resolucion

Endpoint:

    POST /api/tickets/{ticket_id}/resolver

Ejemplo de solicitud:

    {"respuesta": "Se soluciono el inconveniente reportado."}

Una resolucion valida guarda la respuesta del equipo
en `respuesta_atencion` y cambia el estado a `RESUELTO`.

Las operaciones incompatibles con el estado del ticket
se rechazan con HTTP 409.

### Compatibilidad SQLite

El nuevo campo `respuesta_atencion` se agrega al iniciar
la aplicacion si no existe en una base anterior.

La actualizacion conserva los registros existentes.
Las pruebas verifican esta compatibilidad.

### Limitaciones del prototipo

Los responsables son identificadores de equipos de
demostracion. Todavia no existe autenticacion ni control
de permisos para el personal de soporte.

La API no debe exponerse publicamente como servicio
de produccion sin incorporar estas protecciones.
