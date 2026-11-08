# Frontend

Aplicación Angular para la Mesa de Ayuda Inteligente UNAD IA 360.

## Requisitos

- Node.js 24.15 o superior (línea 24)
- npm

## Instalación

Desde el directorio `frontend`:

```powershell
npm ci
```

## Desarrollo

```powershell
npm start
```

La aplicación estará disponible en http://localhost:4200.

## Pruebas

```powershell
npm test -- --watch=false
```

## Compilación

```powershell
npm run build
```

Los archivos de compilación se generan en `dist/`.
## Integracion local con FastAPI

Para comprobar la comunicacion entre Angular y FastAPI,
ejecutar ambos servidores en terminales independientes.

Backend, desde `backend`:

    uv sync
    uv run uvicorn app.main:app --reload

Frontend, desde `frontend`:

    npm ci
    npm start

Abrir http://127.0.0.1:4200/.

La aplicacion consulta `/api/health` y muestra el estado
de conexion con el backend.

En desarrollo, Angular utiliza `src/proxy.conf.json`
para redirigir `/api/health` hacia `http://127.0.0.1:8000/api/health`.

El proxy es exclusivo del servidor de desarrollo.
Un despliegue de produccion necesitara configurar
el enrutamiento de `/api` hacia el backend.

Para ejecutar las pruebas del frontend:

    npm test -- --watch=false

Para comprobar la compilacion:

    npm run build

## Interfaz funcional de Mesa de Ayuda

La aplicacion Angular incorpora tres vistas:

- Vista general: indicadores y solicitudes recientes.
- Mis solicitudes: registro, consulta y confirmacion de soluciones.
- Panel de soporte: atencion y resolucion de tickets.

### Identidad visual

La interfaz utiliza una presentacion institucional inspirada
en la identidad grafica de la UNAD, con recursos SVG locales,
diseno adaptable a dispositivos moviles y sin bibliotecas
visuales adicionales.

### Ejecucion local

Primero iniciar FastAPI desde la carpeta backend:

    uv run --locked python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Despues iniciar Angular desde la carpeta frontend:

    npm start

Abrir http://localhost:4200

Angular utiliza el proxy /api para comunicarse con FastAPI.
El listado de tickets se actualiza periodicamente.

### Validaciones

    npm test -- --watch=false
    npm run build

### Alcance

Esta es una interfaz funcional de demostracion.
No incluye autenticacion ni autorizacion por roles.
Las acciones de soporte deben protegerse antes de publicar
el sistema para usuarios reales.
