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
