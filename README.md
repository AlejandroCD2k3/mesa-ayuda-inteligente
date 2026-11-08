# Mesa de Ayuda Inteligente

Prototipo de mesa de ayuda para el ecosistema UNAD IA 360.

## Tecnologias

- Angular
- FastAPI
- SQLite

## Ramas

- main: produccion
- development: desarrollo e integracion

## Estado

Hito 3 - Preparacion del entorno de desarrollo.

## Documentacion

La especificacion de requisitos y diseno se encuentra en docs/.

## Mesa de Ayuda Inteligente — Guía del prototipo

Prototipo académico de Mesa de Ayuda Inteligente UNAD IA 360.

Permite registrar solicitudes, clasificarlas, sugerir una
solución para consultas frecuentes, recibir la confirmación
del solicitante y atender casos funcionales o técnicos.

### Tecnologías

- Frontend: Angular 22 y TypeScript.
- Backend: FastAPI y Python 3.12.
- Persistencia: SQLite mediante SQLModel.
- Pruebas: Vitest y pytest.

### Requisitos

- Git.
- Python 3.12.
- Gestor de paquetes uv.
- Node.js y npm compatibles con Angular 22.

### Instalación

Clonar el repositorio privado:

    git clone https://github.com/AlejandroCD2k3/mesa-ayuda-inteligente.git

Entrar al proyecto:

    cd mesa-ayuda-inteligente

### Iniciar el backend

En una terminal PowerShell:

    cd backend
    uv sync --locked
    uv run --locked python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Documentación interactiva de la API:

    http://127.0.0.1:8000/docs

### Iniciar el frontend

En otra terminal PowerShell, desde el repositorio:

    cd frontend
    npm ci
    npm start

Abrir en el navegador:

    http://localhost:4200

Angular utiliza el proxy /api para comunicarse
con el backend local.

### Escenarios de demostración

1. Consulta automática: preguntar en MAIA dónde
   encontrar las actividades del curso. Confirmar
   o rechazar la solución sugerida.

2. Escalamiento: rechazar la solución automática
   y completar la atención desde el panel de soporte.

3. Atención funcional: registrar una solicitud
   indicando que no es posible adjuntar una tarea.

4. Atención técnica: registrar un error HTTP 500
   de integración entre EvaluIA y Moodle.

### Ejecutar pruebas

Desde backend:

    uv run --locked python -m pytest -q

Desde frontend:

    npm test -- --watch=false
    npm run build

### Documentación adicional

- docs/aceptacion.md
- backend/README.md
- frontend/README.md

### Alcance y limitaciones

La aplicación es un prototipo de demostración local.

La clasificación se basa en reglas para escenarios
definidos y no utiliza todavía un modelo de lenguaje
para comprender solicitudes generales.

La sugerencia automática está implementada para un
caso específico de consulta de actividades en MAIA.

No existe autenticación ni autorización real por roles.
Los responsables de soporte representan equipos
de demostración.

No debe exponerse públicamente como una aplicación
de producción sin incorporar controles de acceso.

La base SQLite local almacena los tickets registrados.
Los archivos de datos locales no se incluyen en Git.
