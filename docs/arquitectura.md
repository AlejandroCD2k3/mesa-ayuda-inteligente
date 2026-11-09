# Arquitectura de la mesa de ayuda (hexagonal ligera)

- `backend/app/domain`: reglas puras de clasificación, soluciones, permisos y tipos.
- `backend/app/application`: casos de uso para preparar tickets y registrar eventos.
- `backend/app/api`: adaptadores HTTP para tickets y conocimiento.
- `backend/app/infrastructure/ai`: adaptador OpenRouter configurable.
- `backend/app/infrastructure/persistence`: modelos SQLModel de SQLite.
- `backend/app/main.py`: composición de rutas e inicialización.
- `frontend/src/app/core/models.ts`: contratos tipados compartidos.

Se conservan módulos compatibles (`app.models`, `app.ia`, `app.database`, etc.)
para no romper herramientas y pruebas existentes. La separación es incremental:
aún hay casos de uso que reciben modelos SQLModel; no se afirma aislamiento
hexagonal estricto. Los endpoints y el esquema SQLite no cambian.
