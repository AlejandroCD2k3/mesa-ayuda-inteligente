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

### Inicio rapido en Windows

Para iniciar el prototipo completo, hacer doble clic en:

`iniciar-mesa-ayuda.bat`

El iniciador:

- Comprueba que uv y npm esten disponibles.
- Instala las dependencias Angular si faltan.
- Inicia FastAPI en el puerto 8000.
- Inicia Angular en el puerto 4200.
- Espera a que ambos servicios respondan.
- Abre automaticamente el navegador.

Para detener la aplicacion, presionar `Ctrl+C`
en cada una de las dos ventanas de los servidores.

El iniciador esta pensado para el desarrollo y
la demostracion local en Windows.


## Configuracion excepcional de demostracion

Este repositorio contiene una configuracion `.env`
incluida excepcionalmente para facilitar la evaluacion
academica del prototipo Mesa de Ayuda Inteligente
UNAD IA 360.

**Advertencia de seguridad:** esta practica no debe
utilizarse en entornos de produccion ni con claves
personales o permanentes.

La credencial incluida esta destinada exclusivamente
a la demostracion. Quienes tengan acceso al repositorio
pueden verla y utilizarla. Su inclusion en el historial
de Git constituye una exposicion deliberada.

La clave debe revocarse al finalizar la evaluacion.
No debe reutilizarse para otros proyectos.

En un despliegue real, las credenciales deben mantenerse
fuera del repositorio, mediante variables de entorno
o un gestor de secretos.

### Ejecucion de la demostracion

1. Descargar o clonar el repositorio.
2. Instalar las dependencias descritas en este README.
3. Ejecutar `iniciar-mesa-ayuda-demo.bat`.
4. Abrir la direccion local que muestra el lanzador.
5. Utilizar los perfiles de demostracion.

El lanzador de demostracion carga automaticamente
la configuracion de OpenRouter antes de iniciar
la aplicacion. No es necesario introducir otra clave.

El modelo configurado es `openrouter/free`, sujeto
a disponibilidad y limites del servicio.

Si la IA no esta disponible, se utiliza el
clasificador tradicional.

La autenticacion incluida corresponde a un prototipo
academico y no debe exponerse publicamente como
un sistema de produccion.

### Datos ficticios preparados para evaluación

La instalación incluye el catálogo editable `backend/datos_demo.json`,
con 8 artículos publicados y 4 tickets ficticios, con sus eventos.

Para comenzar desde una instalación nueva:

1. Copiar `backend/.env.example` como `backend/.env`.
2. Introducir la clave de prueba en `LLM_API_KEY`.
3. Ejecutar `iniciar-mesa-ayuda-evaluacion.bat`.

Este lanzador agrega los datos automáticamente si la base está vacía.
No modifica una base de datos que ya contiene registros.

Para restaurar manualmente el catálogo de demostración, cerrar
los servidores y ejecutar desde `backend`:

`uv run --locked python -m scripts.preparar_demo --reset`

Esta operación respalda primero SQLite en la carpeta local
`MesaAyuda/respaldos`, fuera del repositorio, y después reemplaza
los artículos, tickets y eventos existentes.

Los datos son ficticios y no representan procedimientos
institucionales oficiales. La clave privada nunca se incluye
en el catálogo ni en GitHub.
